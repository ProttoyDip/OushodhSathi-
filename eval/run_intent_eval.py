"""Evaluate the escalate-only Sathi intent classifier on HUMAN-WRITTEN held-out rows.

  NVIDIA_API_KEY=... python eval/run_intent_eval.py

Reports per-class recall with 95% Wilson intervals for the full Sathi pipeline WITH the classifier
(guard.py first, then the classifier, which can only escalate), and checks that medical recall is not
below what guard.py alone achieves. Writes eval/intent_results.json, which /docs reads.

Until there are at least 200 human-written held-out examples (or no trained model exists), it writes
status "in_progress" and the classifier stays switched off (SATHI_INTENT_MODEL=off).
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "backend" / ".env")

from app import intent_classifier, sathi  # noqa: E402
from app.stats import proportion  # noqa: E402

DATASET = ROOT / "eval" / "intent_dataset.csv"
OUT = ROOT / "eval" / "intent_results.json"
MIN_HELDOUT = 200
EXPECT = {"app": "APP", "medical": "MEDICAL", "emergency": "EMERGENCY"}


def heldout_human() -> list[dict]:
    with DATASET.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["split"] == "heldout" and r["source"] != "synthetic"]


def run(rows: list[dict], with_model: bool) -> dict[str, dict]:
    os.environ["SATHI_INTENT_MODEL"] = "on" if with_model else "off"
    by_label: dict[str, list[bool]] = {}
    for r in rows:
        intent, _ = sathi.classify_question(r["text"], None)
        ok = intent == EXPECT[r["label"]] or (r["label"] == "app" and intent in ("APP", "OTHER"))
        by_label.setdefault(r["label"], []).append(ok)
    return {lab: proportion(lab, sum(v), len(v)) for lab, v in sorted(by_label.items())}


def main() -> None:
    rows = heldout_human()
    status = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "heldout_human": len(rows),
              "required": MIN_HELDOUT, "embed_model": intent_classifier.EMBED_MODEL,
              "model_trained": intent_classifier.MODEL_PATH.exists(), "enabled_in_production": False}
    if len(rows) < MIN_HELDOUT or not intent_classifier.MODEL_PATH.exists():
        status["status"] = "in_progress"
        status["guard_only_recall"] = run(rows, with_model=False)
        OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"evaluation in progress: {len(rows)} of {MIN_HELDOUT} human held-out examples; "
              f"model trained: {status['model_trained']}. The classifier stays off.")
        return
    guard_only, with_model = run(rows, False), run(rows, True)
    medical_ok = with_model.get("medical", {}).get("p", 1) >= guard_only.get("medical", {}).get("p", 1)
    status.update(status="done", guard_only_recall=guard_only, with_model_recall=with_model,
                  medical_recall_not_lower=medical_ok)
    OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    for lab, p in with_model.items():
        print(f"{lab:10} recall {p['p']:.0%} (95% CI {p['ci_low']:.0%}-{p['ci_high']:.0%}), n={p['n']}")
    if not medical_ok:
        sys.exit("FAIL: medical recall dropped below guard.py alone; keep SATHI_INTENT_MODEL=off")


if __name__ == "__main__":
    main()
