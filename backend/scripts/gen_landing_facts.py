"""Writes frontend/src/data/brandFacts.json and evidence.json: the numbers the landing page prints, taken
only from backend/data and the results files in eval/.

The frontend is built on its own (Vercel builds only frontend/), so the page cannot read backend/data at
build time; this file is generated and committed, and tests/test_landing_facts.py fails when it is stale.

  backend/.venv/Scripts/python backend/scripts/gen_landing_facts.py
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend" / "data"
OUT = ROOT / "frontend" / "src" / "data" / "brandFacts.json"
EVIDENCE_OUT = ROOT / "frontend" / "src" / "data" / "evidence.json"
EVAL = ROOT / "eval"


def facts() -> dict:
    with (DATA / "brands_seed.csv").open(encoding="utf-8", newline="") as f:
        seed = [r for r in csv.DictReader(line for line in f if not line.lstrip().startswith("#"))
                if r.get("brand") and r.get("generic")]
    by_generic: dict[str, set[str]] = defaultdict(set)
    for r in seed:
        by_generic[r["generic"].strip().lower()].add(r["brand"].strip())
    full = DATA / "brands_full.csv"
    dataset = 0
    if full.exists():
        with full.open(encoding="utf-8", newline="") as f:
            dataset = sum(1 for r in csv.DictReader(f) if r.get("brand") and r.get("generic"))
    return {
        "seedBrands": len({r["brand"].strip().lower() for r in seed}),
        "seedGenerics": len(by_generic),
        "seedSharedGenerics": sum(1 for b in by_generic.values() if len(b) > 1),
        "datasetBrands": dataset,
        "datasetSource": "Medicinal Products in Bangladesh (Mendeley Data, doi:10.17632/zhtvkny53n.1), CC BY 4.0",
    }


def _rate(r: dict) -> dict:
    return {"k": r["k"], "n": r["n"], "pct": round(100 * r["p"]), "lo": round(100 * r["ci_low"]), "hi": round(100 * r["ci_high"])}


def evidence() -> dict:
    """Measured results only. Real photos come first; the synthetic benchmark is kept apart."""
    def load(name: str) -> dict:
        return json.loads((EVAL / name).read_text(encoding="utf-8"))

    real = load("results_extract_strip.v3.json")["runs"]["chain"]
    synth = load("synthetic/results_extract_strip.v1.json")["runs"]["chain"]
    sathi = load("sathi_results_sathi_bn.v1.json")["by_category"]
    hybrid = load("help_retrieval_results.json")["methods"]["hybrid"]["recall@1"]
    cond = real["by_condition"]
    return {
        "realPhotos": real["photos"],
        "realBrand": _rate(real["brand"]),
        "realStrength": _rate(real["strength"]),
        "realBangla": {"k": cond["bangla"]["k"], "n": cond["bangla"]["n"]},
        "realClear": {"k": cond["clear"]["k"], "n": cond["clear"]["n"]},
        "syntheticBrand": _rate(synth["brand"]),
        "sathiMedical": {"k": sathi["medical"]["correct"], "n": sathi["medical"]["n"]},
        "sathiEmergency": {"k": sathi["emergency"]["correct"], "n": sathi["emergency"]["n"]},
        "retrieval": _rate(hybrid),
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(facts(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    EVIDENCE_OUT.write_text(json.dumps(evidence(), indent=2, ensure_ascii=False) + chr(10), encoding="utf-8")
    print(f"wrote {OUT} and {EVIDENCE_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
