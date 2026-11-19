"""BP monitor photo eval: read labelled photos of home blood-pressure monitors.

  backend/.venv/Scripts/python eval/run_bp_eval.py          (Windows)
  backend/.venv/bin/python eval/run_bp_eval.py              (macOS/Linux)
  ... eval/run_bp_eval.py --kind synthetic --labels eval/synthetic/bp_labels.csv

Options: --labels PATH (default eval/bp_labels.csv), --out PATH, --kind real|synthetic; image_path is
relative to the labels file's folder; a synthetic run never writes a real results file.

Reads eval/bp_labels.csv (image_path,systolic,diastolic,pulse; image_path relative to
eval/, pulse may be blank). Reports exact-match accuracy per number, how often the
reader asked the family to check, and how often a wrong reading was NOT flagged (the
number that matters for safety). Writes eval/bp_results_<prompt_version>.json.
Needs a vision provider configured in backend/.env. Never prints keys.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
sys.path.insert(0, str(ROOT))  # evalcommon, also when loaded by path in the tests

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT.parent / "backend" / ".env")

from app import prompts  # noqa: E402
from app.clinical import read_bp_photo  # noqa: E402
from app.llm_router import NoProviderAvailable, Router  # noqa: E402
from evalcommon import LabelError, check_bp_rows, parse, provenance, read_rows  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    version = prompts.version("read_bp")
    a = parse(argv, default_labels="bp_labels.csv", out_name=f"bp_results_{version}.json", per_provider=False)
    try:
        rows = read_rows(a.labels, ("image_path", "systolic", "diastolic", "pulse"))
        check_bp_rows(rows, a.base)
    except LabelError as e:
        print(e)
        return 3
    if not rows:
        print(f"No labelled BP photos yet in {a.labels.name} (see eval/README.md).")
        return 0
    router = Router()
    results = []
    for r in rows:
        photo = (a.base / r["image_path"]).read_bytes()
        try:
            out = read_bp_photo(photo, router)
        except NoProviderAvailable as e:
            print(f"no vision provider: {e}")
            return 1
        want = {k: int(r[k]) if r.get(k) else None for k in ("systolic", "diastolic", "pulse")}
        exact = {k: out[k] == want[k] for k in want if want[k] is not None}
        all_right = all(exact.values())
        results.append({"image": r["image_path"], "want": want, "got": {k: out[k] for k in want},
                        "exact": exact, "needs_check": out["needs_check"],
                        "silent_error": not all_right and not out["needs_check"]})
    n = len(results)

    def rate(key: str) -> float | None:
        vals = [x["exact"][key] for x in results if key in x["exact"]]
        return round(sum(vals) / len(vals), 3) if vals else None

    summary = {
        "prompt_version": version,
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **provenance(a, n),
        "photos": n,
        "systolic_accuracy": rate("systolic"),
        "diastolic_accuracy": rate("diastolic"),
        "pulse_accuracy": rate("pulse"),
        "asked_to_check": round(sum(x["needs_check"] for x in results) / n, 3),
        "wrong_and_not_flagged": sum(x["silent_error"] for x in results),
        "results": results,
    }
    out_path = a.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print({k: v for k, v in summary.items() if k != "results"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
