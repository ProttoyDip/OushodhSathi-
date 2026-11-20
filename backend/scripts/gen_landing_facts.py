"""Writes frontend/src/data/brandFacts.json: the brand-table numbers the landing page prints.

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


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(facts(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
