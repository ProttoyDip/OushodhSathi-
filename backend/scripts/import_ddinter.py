"""Load DDInter 2.0 CSV downloads into backend/data/interactions_ddinter.csv.

DDInter publishes one CSV per ATC group with columns
DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level (Major | Moderate | Minor | Unknown).
Only Major and Moderate rows are kept; the rules engine ignores the rest.
DDInter is CC BY-NC-SA 4.0: non-commercial prototype use with attribution.

Usage:
  python scripts/import_ddinter.py ddinter_downloads_code_A.csv ddinter_downloads_code_B.csv ...
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "interactions_ddinter.csv"
SOURCE = "DDInter 2.0 (CC BY-NC-SA 4.0)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    args = ap.parse_args()
    seen: dict[tuple[str, str], dict[str, str]] = {}
    for path in args.files:
        with path.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                level = (r.get("Level") or "").strip().lower()
                a, b = (r.get("Drug_A") or "").strip().lower(), (r.get("Drug_B") or "").strip().lower()
                if level not in ("major", "moderate") or not a or not b:
                    continue
                key = tuple(sorted((a, b)))
                if key in seen and seen[key]["severity"] == "major":
                    continue
                seen[key] = {"a": key[0], "b": key[1], "severity": level,
                             "effect": f"{level.capitalize()} interaction listed in DDInter 2.0.",
                             "source": SOURCE, "effect_bn": ""}
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["a", "b", "severity", "effect", "source", "effect_bn"])
        w.writeheader()
        w.writerows(seen.values())
    print(f"wrote {len(seen)} interactions to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
