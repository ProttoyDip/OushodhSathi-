"""Strip-reading accuracy: run the shelf agent on labelled photos and report honest numbers.

  backend/.venv/Scripts/python eval/run_eval.py                  (Windows)
  backend/.venv/bin/python eval/run_eval.py                      (macOS / Linux)
  ... eval/run_eval.py --per-provider                            (also each vision provider alone)
  ... eval/run_eval.py --kind synthetic --labels eval/synthetic/labels.csv   (the synthetic benchmark)

Options: --labels PATH (default eval/labels.csv), --out PATH (default eval/results_<prompt>.json, or next
to the labels for --kind synthetic), --kind real|synthetic. image_path is relative to the labels file's
folder. Real and synthetic results never mix: a synthetic run refuses to write a real results file, and
only real runs are held to the MIN_PHOTOS rule.

Reads eval/labels.csv: image_path,brand,strength,expiry,condition[,source] - one row per medicine visible
in a photo (image_path relative to eval/, expiry YYYY-MM or empty, condition one of cut_strip, glare,
bangla, handwritten, clear; source empty for our own photos, or e.g. mendeley:tg2hm7n2bs for a dataset
prescription). Results are also reported per source. Label photos with backend/scripts/label_photos.py;
pick dataset prescriptions with backend/scripts/pick_prescriptions.py.

Reports, each as a proportion with a 95% Wilson interval:
  brand      the brand was read (normalised exact match)
  strength   brand and strength both right (rows with a labelled strength only)
  expiry     brand and expiry both right (rows with a labelled expiry only)
  needs check  share of correctly found medicines the app would show for a human check
             (confidence below CONFIDENCE_CUTOFF, the app's own cut-off)
plus a reliability table (stated confidence vs observed brand accuracy, to check the 0.75 cut-off),
results by photo condition, and, with --per-provider, each vision provider on its own.
The OCR second reader (backend/app/ocr_check.py) is measured too: of the vision model's wrong strengths
and expiries, how many it flagged (catch rate), and of the right ones, how many it flagged anyway
(false alarms), plus the needs-check rate with it on.
With fewer than MIN_PHOTOS photos the JSON says "evaluation in progress" and /docs shows only that.
Writes eval/results_<prompt_version>.json. Needs a vision provider in backend/.env. Never prints keys.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
sys.path.insert(0, str(ROOT))  # evalcommon, also when loaded by path in the tests

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT.parent / "backend" / ".env")

from app import agent, llm_router, prompts  # noqa: E402
from app.brands import _bn_index, has_bangla, normalise, normalise_bn  # noqa: E402
from app.llm_router import NoProviderAvailable, configured_providers  # noqa: E402
from app.stats import proportion  # noqa: E402
from evalcommon import LabelError, check_strip_rows, parse, provenance, read_rows  # noqa: E402

MIN_PHOTOS = 25            # below this, no accuracy number is shown anywhere
CONFIDENCE_CUTOFF = 0.75   # the app shows anything below this for a human check
BUCKETS = [(0.0, 0.5), (0.5, 0.75), (0.75, 0.9), (0.9, 1.01)]


def norm_strength(s: str | None) -> str:
    return re.sub(r"\s+", "", (s or "").lower())


def brand_key(name: str) -> str:
    """Comparable form of a brand in either script. A Bangla reading is mapped through the same
    pharmacist-checked alias table the app uses (data/brands_bn.csv), so "নাপা" counts as Napa."""
    if has_bangla(name):
        bn = normalise_bn(name)
        alias = _bn_index().get(bn)
        return normalise(alias) if alias else bn
    return normalise(name)


def brand_keys(label: str) -> set[str]:
    """A label may list the same brand in both scripts, "Nasovap|ন্যাসোভ্যাপ": a read of either counts."""
    return {k for k in (brand_key(part) for part in label.split("|")) if k}


def load_labels(path: Path = ROOT / "labels.csv", check_images: bool = False) -> dict[str, list[dict]]:
    """image_path -> its label rows. Older 3- and 5-column files still load (missing columns read as "")."""
    rows = read_rows(path, ("image_path", "brand"))
    if check_images:
        check_strip_rows(rows, path.parent)
    labels: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r.get("image_path") and r.get("brand"):
            labels[r["image_path"]].append(r)
    return labels


def _second_read_gain(flagged_when_wrong: list[bool], flagged_when_right: list[bool], name: str) -> dict:
    """Of the vision model's wrong readings, how many the OCR second reader flagged (catch rate), and of
    its right readings, how many it flagged anyway (false alarms)."""
    w, r = flagged_when_wrong, flagged_when_right
    return {"catch": proportion(f"{name}_catch", sum(w), len(w)) if w else None,
            "false_alarm": proportion(f"{name}_false_alarm", sum(r), len(r)) if r else None}


def score(labels: dict[str, list[dict]], outputs: dict[str, list], seconds: dict[str, list] | None = None,
          default_source: str = "own") -> dict:
    """outputs: image_path -> extracted items (brand, strength, expiry, confidence); seconds: the same
    shape with each item's OCR second-read verdict (or None). Pure; tested."""
    seconds = seconds or {}
    n = brand = strength = str_n = 0
    exp_n = exp_ok = 0
    s_wrong, s_right, e_wrong, e_right = [], [], [], []
    flagged_total = 0
    found_conf: list[float] = []
    by_condition: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_source: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # own photos vs dataset photos
    reliability = [[0, 0] for _ in BUCKETS]  # [correct, total] per confidence bucket
    per_image = []
    for image, expected in labels.items():
        got = outputs.get(image, [])
        srs = seconds.get(image) or [None] * len(got)
        rows = []
        for exp in expected:
            n += 1
            keys = brand_keys(exp["brand"])
            idx = next((i for i, g in enumerate(got) if brand_key(g.brand) in keys), None)
            match = got[idx] if idx is not None else None
            sr = srs[idx] if idx is not None else None
            b_ok = match is not None
            # strength is scored only where the pack prints one (a syrup's "100 ml" is not a strength)
            s_ok = None
            if (exp.get("strength") or "").strip():
                str_n += 1
                s_ok = b_ok and norm_strength(match.strength) == norm_strength(exp.get("strength"))
                strength += s_ok
            brand += b_ok
            e_ok = None
            if (exp.get("expiry") or "").strip():
                exp_n += 1
                e_ok = b_ok and (match.expiry or "") == exp["expiry"].strip()
                exp_ok += e_ok
            if b_ok:
                found_conf.append(match.confidence)
            if b_ok and sr:  # the second reader ran on this photo
                s_flag, e_flag = sr.get("strength") == "disagree", sr.get("expiry") == "disagree"
                if s_ok is not None:
                    (s_right if s_ok else s_wrong).append(s_flag)
                if e_ok is not None:
                    (e_right if e_ok else e_wrong).append(e_flag)
                flagged_total += (s_flag or e_flag or match.confidence < CONFIDENCE_CUTOFF)
            cond = (exp.get("condition") or "unlabelled").strip() or "unlabelled"
            by_condition[cond][0] += b_ok
            by_condition[cond][1] += 1
            src = (exp.get("source") or "").strip() or default_source
            by_source[src][0] += b_ok
            by_source[src][1] += 1
            rows.append({"expected": exp, "brand_ok": b_ok, "strength_ok": s_ok,
                         "got": match.model_dump() if match else None})
        wanted = set().union(*(brand_keys(e["brand"]) for e in expected))
        for g in got:  # every extracted item: was the brand it claims really there?
            i = next(k for k, (lo, hi) in enumerate(BUCKETS) if lo <= g.confidence < hi)
            reliability[i][0] += brand_key(g.brand) in wanted
            reliability[i][1] += 1
        per_image.append({"image": image, "results": rows,
                          "extra_items": [g.brand for g in got if brand_key(g.brand) not in wanted]})
    low = sum(c < CONFIDENCE_CUTOFF for c in found_conf)
    return {
        "photos": len(labels), "labelled_items": n,
        "brand": proportion("brand", brand, n) if n else None,
        "strength": proportion("strength", strength, str_n) if str_n else None,
        "expiry": proportion("expiry", exp_ok, exp_n) if exp_n else None,
        "needs_check": proportion("needs_check", low, len(found_conf)) if found_conf else None,
        # the OCR second reader (app/ocr_check.py): how many vision mistakes it caught, at what cost
        "second_read": {
            "ran_on_items": len(s_wrong) + len(s_right),
            "strength": _second_read_gain(s_wrong, s_right, "strength"),
            "expiry": _second_read_gain(e_wrong, e_right, "expiry"),
            "needs_check_with_second_read": (proportion("needs_check_2", flagged_total, len(s_wrong) + len(s_right))
                                             if s_wrong or s_right else None),
        },
        "reliability": [{"confidence": f"{lo:.2f}-{min(hi, 1):.2f}", "items": t,
                         "observed": proportion("observed", c, t) if t else None}
                        for (lo, hi), (c, t) in zip(BUCKETS, reliability)],
        "by_condition": {k: proportion(k, ok, t) for k, (ok, t) in sorted(by_condition.items())},
        "by_source": {k: proportion(k, ok, t) for k, (ok, t) in sorted(by_source.items())},
        "avg_confidence": round(sum(found_conf) / len(found_conf), 3) if found_conf else None,
        "per_image": per_image,
    }


METRICS = ("brand", "strength", "expiry", "needs_check")


def mark_answers(run: dict) -> dict:
    """Separates a provider that failed from one that read badly. `photos_without_answer` counts photos
    where nothing at all came back. If the provider never answered (no model id, every photo empty), the
    run is marked "no answer" and its accuracy fields are cleared, so a rate limit is never shown as 0%."""
    empty = sum(1 for img in run.get("per_image", [])
                if not any(r.get("got") for r in img.get("results", [])) and not img.get("extra_items"))
    run["photos_without_answer"] = empty
    if run.get("model_id") is None and empty == run.get("photos"):
        run["status"] = "no answer: every request failed (rate limit or provider error) - not an accuracy result"
        for k in METRICS:
            run[k] = None
        run["by_condition"], run["by_source"] = {}, {}
    return run


async def extract_all(labels: dict[str, list[dict]], base: Path = ROOT) -> tuple[dict[str, list], dict[str, list], str | None]:
    outputs, seconds, model_id = {}, {}, None
    for image in labels:
        outcome = await agent.read_shelf([(base / image).read_bytes()])
        model_id = model_id or outcome.model_id
        outputs[image] = [s.item for s in outcome.items]
        seconds[image] = [s.match.get("second_read") for s in outcome.items]
        print(f"  {image}: {len(outputs[image])} read")
    return outputs, seconds, model_id


async def main(argv: list[str] | None = None) -> int:
    version = prompts.version("extract_strip")
    a = parse(argv, default_labels="labels.csv", out_name=f"results_{version}.json")
    try:
        labels = load_labels(a.labels, check_images=True)
    except LabelError as e:
        print(e)
        return 3
    if not labels:
        print(f"{a.labels.name} has no rows yet. Label photos with backend/scripts/label_photos.py (see eval/README.md).")
        return 1
    try:
        print(f"chain (as the app runs it) · {a.kind} · {a.labels}")
        outputs, seconds, model_id = await extract_all(labels, a.base)
        src = "synthetic" if a.kind == "synthetic" else "own"
        runs = {"chain": mark_answers({"model_id": model_id, **score(labels, outputs, seconds, src)})}
        if a.per_provider:
            for p in configured_providers("vision"):
                print(f"{p.name} / {p.model} alone")
                only = lambda *_a, _p=p, **_k: [_p]  # noqa: E731
                agent.configured_providers = only
                llm_router.configured_providers = only
                outs, secs, mid = await extract_all(labels, a.base)
                runs[f"{p.name}/{p.model}"] = mark_answers({"model_id": mid, **score(labels, outs, secs, src)})
    except NoProviderAvailable as e:
        print(f"No vision provider available: {e}")
        return 2

    chain = runs["chain"]
    # the real-photo minimum applies to real photos only; a synthetic run always reports, labelled as such
    enough = a.kind == "synthetic" or len(labels) >= MIN_PHOTOS
    status = ("synthetic benchmark" if a.kind == "synthetic" else
              "measured" if enough else f"evaluation in progress (n = {len(labels)} photos; {MIN_PHOTOS} needed)")
    summary = {
        "prompt_version": version, "model_id": chain["model_id"],
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **provenance(a, len(labels)),
        "status": status,
        "images": len(labels), "labelled_items": chain["labelled_items"],
        # point estimates for /docs and the README, only once there are enough photos
        "brand_accuracy": chain["brand"]["p"] if enough else None,
        "strength_accuracy": chain["strength"]["p"] if enough else None,
        "avg_confidence": chain["avg_confidence"],
        "confidence_cutoff": CONFIDENCE_CUTOFF,
        "runs": runs,
    }
    out = a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    for name, r in runs.items():
        print(f"\n{name}  ({r['photos']} photos, {r['labelled_items']} medicines, "
              f"{r['photos_without_answer']} with no answer)")
        if r.get("status", "").startswith("no answer"):
            print(f"  {r['status']}")
            continue
        for key in ("brand", "strength", "expiry", "needs_check"):
            v = r[key]
            if v:
                print(f"  {key:12} {v['k']}/{v['n']} = {v['p']:.0%}  (95% CI {v['ci_low']:.0%}-{v['ci_high']:.0%})")
        sr = r["second_read"]
        for key in ("strength", "expiry"):
            for part in ("catch", "false_alarm"):
                v = sr[key][part]
                if v:
                    print(f"  2nd read {key} {part:11} {v['k']}/{v['n']} = {v['p']:.0%}  (95% CI {v['ci_low']:.0%}-{v['ci_high']:.0%})")
        for src, v in r["by_source"].items():
            print(f"  source {src:22} brand {v['k']}/{v['n']} = {v['p']:.0%}  (95% CI {v['ci_low']:.0%}-{v['ci_high']:.0%})")
        print("  reliability  " + "  ".join(
            f"{b['confidence']}: {b['observed']['p']:.0%} of {b['items']}" for b in r["reliability"] if b["observed"]))
    print(f"\n{summary['status']}\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
