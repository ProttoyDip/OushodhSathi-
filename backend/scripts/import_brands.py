"""Convert the "Medicinal Products in Bangladesh" dataset (Md Mahmudur Rahman and Md M Khan,
University of Dhaka; Mendeley Data v1, 2024; doi:10.17632/zhtvkny53n.1; CC BY 4.0) into
backend/data/brands_full.csv (brand,generic,drug_class,manufacturer,verified,note).

The dataset ships a medicine table (brand name, generic, strength, manufacturer, ...)
and, in some versions, a generic table with the drug class. Column names differ
between versions (v1 uses camelCase: brandName, genericName, dosageType), so they are
detected case-insensitively from a list of candidates.

One row per brand. A brand sold in several forms keeps the row of a tablet or capsule
(what a family photographs on a strip), else the first row. Every row is verified=no:
the curated seed (brands_seed.csv) always takes priority in app/tables.py.

Usage:
  python scripts/import_brands.py path/to/medicine.csv [--generics path/to/generic.csv]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "brands_full.csv"

BRAND_COLS = ("brand name", "brandname", "brand", "brand_name", "name")
GENERIC_COLS = ("generic", "generic name", "genericname", "generic_name")
MAKER_COLS = ("manufacturer", "manufacturer name", "manufacturername", "company")
FORM_COLS = ("dosage form", "dosageform", "dosagetype", "dosage type", "form")
NOTE = "Medicinal Products in Bangladesh (Mendeley Data, doi:10.17632/zhtvkny53n.1) - not pharmacist-verified"
SOLID = ("tablet", "capsule")
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
    solid: set[str] = set()       # brands whose kept row is a tablet/capsule
    generics: dict[str, set[str]] = {}
    read = skipped_empty = 0
    with args.medicines.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            read += 1
            brand, generic = pick(r, BRAND_COLS), pick(r, GENERIC_COLS).lower()
            if not brand or not generic or brand.lower() in BRAND_COLS:
                skipped_empty += 1   # empty brand/generic, or a repeated header line
                continue
            key = brand.lower()
            generics.setdefault(key, set()).add(generic)
            is_solid = any(w in pick(r, FORM_COLS).lower() for w in SOLID)
            if key in rows and (key in solid or not is_solid):
                continue
            rows[key] = {
                "brand": brand,
                "generic": generic,
                "drug_class": pick(r, CLASS_COLS) or classes.get(generic, ""),
                "manufacturer": pick(r, MAKER_COLS),
                "verified": "no",
                "note": NOTE,
            }
            if is_solid:
                solid.add(key)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["brand", "generic", "drug_class", "manufacturer", "verified", "note"])
        w.writeheader()
        w.writerows(rows.values())
    kept = read - skipped_empty
    print(f"read {read} rows; skipped {skipped_empty} (empty brand or generic, or header lines)")
    print(f"collapsed {kept - len(rows)} rows into brands already seen (same brand, other forms/strengths)")
    print(f"{sum(len(g) > 1 for g in generics.values())} brands list more than one generic; kept the tablet/capsule row")
    print(f"wrote {len(rows)} brands to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
