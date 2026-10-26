"""Convert the "Medicinal Products in Bangladesh" dataset (Mendeley Data) into
backend/data/brands_full.csv (brand,generic,drug_class,manufacturer,verified,note).

The dataset ships a medicine table (brand name, generic, strength, manufacturer, ...)
and, in some versions, a generic table with the drug class. Column names differ
between versions, so they are detected case-insensitively.

Usage:
  python scripts/import_brands.py path/to/medicine.csv [--generics path/to/generic.csv]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "brands_full.csv"

BRAND_COLS = ("brand name", "brand", "brand_name", "name")
GENERIC_COLS = ("generic", "generic name", "generic_name")
MAKER_COLS = ("manufacturer", "manufacturer name", "company")
CLASS_COLS = ("drug class", "drug_class", "therapeutic class", "class")


def pick(row: dict[str, str], names: tuple[str, ...]) -> str:
    lowered = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
    for n in names:
        if lowered.get(n):
            return lowered[n]
    return ""


def load_classes(path: Path | None) -> dict[str, str]:
    if not path:
        return {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {pick(r, GENERIC_COLS + ("name",)).lower(): pick(r, CLASS_COLS) for r in csv.DictReader(f)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("medicines", type=Path)
    ap.add_argument("--generics", type=Path, default=None)
    args = ap.parse_args()
    classes = load_classes(args.generics)
    rows: dict[str, dict[str, str]] = {}
    with args.medicines.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            brand, generic = pick(r, BRAND_COLS), pick(r, GENERIC_COLS).lower()
            if not brand or not generic:
                continue
            rows.setdefault(brand.lower(), {
                "brand": brand,
                "generic": generic,
                "drug_class": pick(r, CLASS_COLS) or classes.get(generic, ""),
                "manufacturer": pick(r, MAKER_COLS),
                "verified": "no",
                "note": "Medicinal Products in Bangladesh (Mendeley Data) - not pharmacist-verified",
            })
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["brand", "generic", "drug_class", "manufacturer", "verified", "note"])
        w.writeheader()
        w.writerows(rows.values())
    print(f"wrote {len(rows)} brands to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
