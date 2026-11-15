"""Sathi app-guide retrieval: keyword-only vs vector-only vs hybrid (RRF).

  python eval/run_retrieval_eval.py          # needs NVIDIA_API_KEY for the vector and hybrid rows
  python eval/run_retrieval_eval.py --index  # (re)build the local vector index first

Reads eval/help_retrieval_cases.csv (question, lang, expected_entry_id, source) and reports recall@1
and recall@3 with 95% Wilson intervals for each method, per language group, and the vector cosine of
correct vs incorrect top hits (used to set HELP_VECTOR_ACCEPT). Writes eval/help_retrieval_results.json.
Rows with source=draft were written by the build agent and are to be checked or replaced by the team;
the JSON reports how many of each kind were used. Medical questions are not here: guard.py routes them
to a person before retrieval, and run_sathi_eval.py checks that.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("OUSHODH_DB", str(ROOT / "eval" / ".retrieval_index.db"))  # never the live database
os.environ["DATABASE_URL"] = ""

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "backend" / ".env", override=False)
os.environ["DATABASE_URL"] = ""

from app import embeddings, help_index, help_vectors  # noqa: E402
from app.stats import proportion  # noqa: E402
from app.store import Store  # noqa: E402

CASES = ROOT / "eval" / "help_retrieval_cases.csv"
OUT = ROOT / "eval" / "help_retrieval_results.json"


def recall(rows: list[dict], ranked: list[list[str]], at: int) -> dict:
    k = sum(r["expected_entry_id"] in ids[:at] for r, ids in zip(rows, ranked))
    return proportion(f"recall@{at}", k, len(rows))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", action="store_true")
    a = ap.parse_args()
    rows = list(csv.DictReader(CASES.open(encoding="utf-8")))
    store = Store(os.environ["OUSHODH_DB"])
    out = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "cases": len(rows),
           "sources": dict(Counter(r["source"] for r in rows)), "embed_model": embeddings.MODEL,
           "embed_dim": embeddings.DIM, "rrf_k": help_index.RRF_K, "vector_accept": help_index.VECTOR_ACCEPT,
           "methods": {}}
    keyword = [[h.entry.id for h in help_index.keyword_search(r["question"])] for r in rows]
    out["methods"]["keyword"] = {"recall@1": recall(rows, keyword, 1), "recall@3": recall(rows, keyword, 3)}
    if embeddings.configured():
        if a.index or help_vectors.count(store) == 0:
            print("index:", help_vectors.build_index(store))
        help_vectors.attach(store)
        vec = [help_vectors.search(r["question"], k=10, store=store) for r in rows]
        vector = [[i for i, _ in v] for v in vec]
        hybrid = [[h.entry.id for h in help_index.search(r["question"], k=3)] for r in rows]
        out["methods"]["vector"] = {"recall@1": recall(rows, vector, 1), "recall@3": recall(rows, vector, 3)}
        out["methods"]["hybrid"] = {"recall@1": recall(rows, hybrid, 1), "recall@3": recall(rows, hybrid, 3)}
        right = sorted(round(v[0][1], 3) for r, v in zip(rows, vec) if v and v[0][0] == r["expected_entry_id"])
        wrong = sorted(round(v[0][1], 3) for r, v in zip(rows, vec) if v and v[0][0] != r["expected_entry_id"])
        out["vector_top1_cosine"] = {"correct": right, "incorrect": wrong}
        by_lang = {}
        for lang in sorted({r["lang"] for r in rows}):
            idx = [i for i, r in enumerate(rows) if r["lang"] == lang]
            sub = [rows[i] for i in idx]
            by_lang[lang] = {m: recall(sub, [ranked[i] for i in idx], 1)
                             for m, ranked in (("keyword", keyword), ("vector", vector), ("hybrid", hybrid))}
        out["recall@1_by_language"] = by_lang
    else:
        out["note"] = "NVIDIA_API_KEY not set: keyword row only"
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    for m, v in out["methods"].items():
        r1, r3 = v["recall@1"], v["recall@3"]
        print(f"{m:8} recall@1 {r1['k']}/{r1['n']} = {r1['p']:.0%} (95% CI {r1['ci_low']:.0%}-{r1['ci_high']:.0%})  "
              f"recall@3 {r3['p']:.0%} (95% CI {r3['ci_low']:.0%}-{r3['ci_high']:.0%})")


if __name__ == "__main__":
    main()
