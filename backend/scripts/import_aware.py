"""Convert the WHO AWaRe spreadsheet into backend/data/aware_2025.csv.

Source: WHO, "The selection and use of essential medicines, 2025: WHO AWaRe classification",
https://www.who.int/publications/i/item/B09489 (download the Excel file into backend/data/raw/).
LICENCE: CC BY-NC-SA 3.0 IGO (non-commercial). The header of the output file says so.

Usage:
  python scripts/import_aware.py backend/data/raw/<WHO file>.xlsx      # needs: pip install openpyxl
  python scripts/import_aware.py backend/data/raw/<sheet exported>.csv

The script looks for a column whose header contains "antibiotic" (the medicine) and one that
contains "category" or "aware" (Access / Watch / Reserve). Rows with any other value are
skipped and counted, so nothing is guessed.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "aware_2025.csv"
GROUPS = {"access": "Access", "watch": "Watch", "reserve": "Reserve"}
HEADER = [
    '# WHO AWaRe classification of antibiotics. Source: WHO, "The selection and use of essential medicines, 2025: '
    'WHO AWaRe classification", https://www.who.int/publications/i/item/B09489',
    "# LICENCE: CC BY-NC-SA 3.0 IGO (non-commercial, share-alike). Do not use in a commercial product without "
    "permission from WHO.",
]


def rows_from(path: Path) -> list[list[str]]:
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        try:
            from openpyxl import load_workbook
        except ImportError:
            sys.exit("Reading .xlsx needs openpyxl: pip install openpyxl (or export the sheet to CSV first)")
        wb = load_workbook(path, read_only=True, data_only=True)
        out: list[list[str]] = []
        for ws in wb.worksheets:
            out += [["" if c is None else str(c) for c in row] for row in ws.iter_rows(values_only=True)]
        return out
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [row for row in csv.reader(f)]


def normalise(name: str) -> str:
    """"Amoxicillin/clavulanic-acid" -> "amoxicillin + clavulanic acid"."""
    name = name.strip().lower().replace("/", " + ").replace("-", " ")
    return " + ".join(" ".join(part.split()) for part in name.split("+") if part.strip())


def main(src: str) -> None:
    rows = rows_from(Path(src))
    header_at = next((i for i, r in enumerate(rows)
                      if any("antibiotic" in c.lower() for c in r) and
                      any(("category" in c.lower() or "aware" in c.lower()) for c in r)), None)
    if header_at is None:
        sys.exit("No header row with an 'antibiotic' column and a 'category'/'AWaRe' column was found")
    header = [c.lower() for c in rows[header_at]]
    name_col = next(i for i, c in enumerate(header) if "antibiotic" in c)
    group_col = next(i for i, c in enumerate(header) if "category" in c or "aware" in c)
    seen: dict[str, str] = {}
    skipped = 0
    for r in rows[header_at + 1:]:
        if len(r) <= max(name_col, group_col) or not r[name_col].strip():
            continue
        group = GROUPS.get(r[group_col].strip().lower())
        if group is None:
            skipped += 1
            continue
        seen[normalise(r[name_col])] = group
    with OUT.open("w", encoding="utf-8", newline="") as f:
        f.write("\n".join(HEADER) + "\n")
        w = csv.writer(f)
        w.writerow(["generic", "group", "source"])
        for generic, group in sorted(seen.items()):
            w.writerow([generic, group, "WHO AWaRe 2025 (imported)"])
    print(f"wrote {len(seen)} antibiotics to {OUT} ({skipped} rows skipped: no Access/Watch/Reserve value)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
