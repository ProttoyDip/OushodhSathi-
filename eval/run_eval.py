"""Strip-reading accuracy: run the shelf agent on labelled photos and report honest numbers.

  backend/.venv/Scripts/python eval/run_eval.py                  (Windows)
  backend/.venv/bin/python eval/run_eval.py                      (macOS / Linux)
  ... eval/run_eval.py --per-provider                            (also each vision provider alone)

Reads eval/labels.csv: image_path,brand,strength,expiry,condition - one row per medicine visible in a
photo (image_path relative to eval/, expiry YYYY-MM or empty, condition one of cut_strip, glare,
bangla, handwritten, clear). Label photos with backend/scripts/label_photos.py.

Reports, each as a proportion with a 95% Wilson interval:
  brand      the brand was read (normalised exact match)
  strength   brand and strength both right
  expiry     brand and expiry both right (rows with a labelled expiry only)
  needs check  share of correctly found medicines the app would show for a human check
             (confidence below CONFIDENCE_CUTOFF, the app's own cut-off)
plus a reliability table (stated confidence vs observed brand accuracy, to check the 0.75 cut-off),
results by photo condition, and, with --per-provider, each vision provider on its own.
With fewer than MIN_PHOTOS photos the JSON says "evaluation in progress" and /docs shows only that.
Writes eval/results_<prompt_version>.json. Needs a vision provider in backend/.env. Never prints keys.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT.parent / "backend" / ".env")

from app import agent, llm_router, prompts  # noqa: E402
from app.brands import normalise  # noqa: E402
from app.llm_router import NoProviderAvailable, configured_providers  # noqa: E402
from app.stats import proportion  # noqa: E402

MIN_PHOTOS = 25            # below this, no accuracy number is shown anywhere
CONFIDENCE_CUTOFF = 0.75   # the app shows anything below this for a human check
BUCKETS = [(0.0, 0.5), (0.5, 0.75), (0.75, 0.9), (0.9, 1.01)]


def norm_strength(s: str | None) -> str:
    return re.sub(r"\s+", "", (s or "").lower())


def load_labels(path: Path = ROOT / "labels.csv") -> dict[str, list[dict]]:
    labels: dict[str, list[dict]] = defaultdict(list)
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("image_path") and r.get("brand"):
                labels[r["image_path"]].append(r)
    return labels


def score(labels: dict[str, list[dict]], outputs: dict[str, list]) -> dict:
    """outputs: image_path -> extracted items (brand, strength, expiry, confidence). Pure; tested."""
    n = brand = strength = 0
    exp_n = exp_ok = 0
    found_conf: list[float] = []
    by_condition: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    reliability = [[0, 0] for _ in BUCKETS]  # [correct, total] per confidence bucket
    per_image = []
    for image, expected in labels.items():
        got = outputs.get(image, [])
        rows = []
        for exp in expected:
            n += 1
            match = next((g for g in got if normalise(g.brand) == normalise(exp["brand"])), None)
            b_ok = match is not None
            s_ok = b_ok and norm_strength(match.strength) == norm_strength(exp.get("strength"))
            brand += b_ok
            strength += s_ok
            if (exp.get("expiry") or "").strip():
                exp_n += 1
                exp_ok += b_ok and (match.expiry or "") == exp["expiry"].strip()
            if b_ok:
                found_conf.append(match.confidence)
            cond = (exp.get("condition") or "unlabelled").strip() or "unlabelled"
            by_condition[cond][0] += b_ok
            by_condition[cond][1] += 1
            rows.append({"expected": exp, "brand_ok": b_ok, "strength_ok": s_ok,
                         "got": match.model_dump() if match else None})
        wanted = {normalise(e["brand"]) for e in expected}
        for g in got:  # every extracted item: was the brand it claims really there?
            i = next(k for k, (lo, hi) in enumerate(BUCKETS) if lo <= g.confidence < hi)
            reliability[i][0] += normalise(g.brand) in wanted
            reliability[i][1] += 1
        per_image.append({"image": image, "results": rows,
                          "extra_items": [g.brand for g in got if normalise(g.brand) not in wanted]})
    low = sum(c < CONFIDENCE_CUTOFF for c in found_conf)
    return {
        "photos": len(labels), "labelled_items": n,
        "brand": proportion("brand", brand, n) if n else None,
        "strength": proportion("strength", strength, n) if n else None,
        "expiry": proportion("expiry", exp_ok, exp_n) if exp_n else None,
        "needs_check": proportion("needs_check", low, len(found_conf)) if found_conf else None,
        "reliability": [{"confidence": f"{lo:.2f}-{min(hi, 1):.2f}", "items": t,
                         "observed": proportion("observed", c, t) if t else None}
                        for (lo, hi), (c, t) in zip(BUCKETS, reliability)],
        "by_condition": {k: proportion(k, ok, t) for k, (ok, t) in sorted(by_condition.items())},
        "avg_confidence": round(sum(found_conf) / len(found_conf), 3) if found_conf else None,
        "per_image": per_image,
    }


async def extract_all(labels: dict[str, list[dict]]) -> tuple[dict[str, list], str | None]:
    outputs, model_id = {}, None
    for image in labels:
        outcome = await agent.read_shelf([(ROOT / image).read_bytes()])
        model_id = model_id or outcome.model_id
        outputs[image] = [s.item for s in outcome.items]
        print(f"  {image}: {len(outputs[image])} read")
    return outputs, model_id


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-provider", action="store_true")
    a = ap.parse_args()
    labels = load_labels()
    if not labels:
        print("eval/labels.csv has no rows yet. Label photos with backend/scripts/label_photos.py (see eval/README.md).")
        return 1
    try:
        print("chain (as the app runs it)")
        outputs, model_id = await extract_all(labels)
        runs = {"chain": {"model_id": model_id, **score(labels, outputs)}}
        if a.per_provider:
            for p in configured_providers("vision"):
                print(f"{p.name} / {p.model} alone")
                only = lambda *_a, _p=p, **_k: [_p]  # noqa: E731
                agent.configured_providers = only
                llm_router.configured_providers = only
                outs, mid = await extract_all(labels)
                runs[f"{p.name}/{p.model}"] = {"model_id": mid, **score(labels, outs)}
    except NoProviderAvailable as e:
        print(f"No vision provider available: {e}")
        return 2

    chain = runs["chain"]
    version = prompts.version("extract_strip")
    enough = len(labels) >= MIN_PHOTOS
    summary = {
        "prompt_version": version, "model_id": chain["model_id"],
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "measured" if enough else f"evaluation in progress (n = {len(labels)} photos; {MIN_PHOTOS} needed)",
        "images": len(labels), "labelled_items": chain["labelled_items"],
        # point estimates for /docs and the README, only once there are enough photos
        "brand_accuracy": chain["brand"]["p"] if enough else None,
        "strength_accuracy": chain["strength"]["p"] if enough else None,
        "avg_confidence": chain["avg_confidence"],
        "confidence_cutoff": CONFIDENCE_CUTOFF,
        "runs": runs,
    }
    out = ROOT / f"results_{version}.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    for name, r in runs.items():
        print(f"\n{name}  ({r['photos']} photos, {r['labelled_items']} medicines)")
        for key in ("brand", "strength", "expiry", "needs_check"):
            v = r[key]
            if v:
                print(f"  {key:12} {v['k']}/{v['n']} = {v['p']:.0%}  (95% CI {v['ci_low']:.0%}-{v['ci_high']:.0%})")
        print("  reliability  " + "  ".join(
            f"{b['confidence']}: {b['observed']['p']:.0%} of {b['items']}" for b in r["reliability"] if b["observed"]))
    print(f"\n{summary['status']}\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
