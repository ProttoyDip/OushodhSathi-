"""Reviewer case summary: v1 (medicine list + findings) vs v2 (Graph RAG, every sentence cited).

  python eval/run_case_summary_eval.py            # needs a text model key in backend/.env
  python eval/run_case_summary_eval.py --runs 10

Seeds the demo household into a throwaway SQLite file (never the live database), then asks each
prompt version for a summary `--runs` times. For each version it reports how often a summary passed
every check (with a 95% Wilson interval), why the others were dropped, how many sentences survived,
how many uncited sentences v2's validator removed, and the median time. The patient's name is never
sent (both versions send age only). Writes eval/case_summary_results.json.
This measures safety-check pass rate and grounding, not clinical usefulness: that needs pharmacists.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "backend" / ".env", override=False)
os.environ["DATABASE_URL"] = ""  # never the live database

from app import clinical, prompts  # noqa: E402
from app.demo_seed import seed_demo  # noqa: E402
from app.llm_router import Router, configured_providers  # noqa: E402
from app.stats import proportion  # noqa: E402
from app.store import Store  # noqa: E402
from app.refills import counts  # noqa: E402

OUT = ROOT / "eval" / "case_summary_results.json"


def run(fn, label: str, n: int, args) -> dict:
    produced, reasons, sentences, uncited, secs, example = 0, Counter(), [], 0, [], None
    for _ in range(n):
        t0 = time.perf_counter()
        out = fn(*args)
        secs.append(time.perf_counter() - t0)
        if out["summary"]:
            produced += 1
            sentences.append(len(out["summary"]["summary"]))
            uncited += out.get("uncited_dropped", 0)
            example = example or {k: out.get(k) for k in ("summary", "facts", "source")}
        else:
            reasons[out["dropped"] or "unknown"] += 1
    return {"prompt_version": prompts.version(label), "runs": n,
            "passed_all_checks": proportion("passed", produced, n),
            "drop_reasons": dict(reasons),
            "mean_sentences_kept": round(statistics.mean(sentences), 2) if sentences else None,
            "uncited_sentences_removed": uncited if label == "case_summary_graph" else None,
            "median_seconds": round(statistics.median(secs), 2), "example": example}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    a = ap.parse_args()
    if not configured_providers("text"):
        sys.exit("No text model configured in backend/.env: nothing to compare.")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:  # Windows keeps the SQLite file open
        store = Store(Path(tmp) / "case_summary_eval.db")
        pid = seed_demo(store)["patient_id"]
        p = store.get_patient(pid)
        items = [it for it in store.list_items(pid, confirmed_only=True) if counts(it)]
        flags = store.list_flags(pid, statuses=("pending_review", "confirmed"))
        router = Router(store=None)  # no response cache: every run is a real model call
        out = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "household": "demo seed", "medicines": len(items), "findings": len(flags),
               "v1": run(clinical.case_summary, "case_summary", a.runs, (p, items, flags, router)),
               "v2_graph_rag": run(clinical.case_summary_graph, "case_summary_graph", a.runs, (p, items, flags, router))}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    for k in ("v1", "v2_graph_rag"):
        r = out[k]
        pa = r["passed_all_checks"]
        print(f"{k:13} passed {pa['k']}/{pa['n']} (95% CI {pa['ci_low']:.0%}-{pa['ci_high']:.0%})  "
              f"sentences {r['mean_sentences_kept']}  median {r['median_seconds']}s  drops {r['drop_reasons']}")


if __name__ == "__main__":
    main()
