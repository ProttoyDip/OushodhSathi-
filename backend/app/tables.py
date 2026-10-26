"""Loads the reference tables in backend/data/. The rules engine receives these as
plain data so that rules.py itself stays free of I/O."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass(frozen=True)
class BrandRow:
    brand: str
    generic: str
    drug_class: str
    manufacturer: str
    verified: bool
    note: str
    source_file: str


@dataclass(frozen=True)
class InteractionRow:
    a: str
    b: str
    severity: str  # major | moderate | minor
    effect: str
    source: str
    effect_bn: str = ""


@dataclass(frozen=True)
class BeersRow:
    target: str
    reason: str
    recommendation: str
    reason_bn: str = ""


@dataclass(frozen=True)
class RuleTables:
    interactions: tuple[InteractionRow, ...] = ()
    beers: tuple[BeersRow, ...] = ()
    duplicate_classes: frozenset[str] = field(default_factory=frozenset)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


@lru_cache(maxsize=1)
def load_brands() -> dict[str, BrandRow]:
    """Brand name (lowercase) -> row. brands_full.csv, if present, overrides the seed."""
    out: dict[str, BrandRow] = {}
    for name in ("brands_seed.csv", "brands_full.csv"):
        path = DATA_DIR / name
        if not path.exists():
            continue
        for r in _read_csv(path):
            if not r.get("brand") or not r.get("generic"):
                continue
            out[r["brand"].lower()] = BrandRow(
                brand=r["brand"],
                generic=r["generic"].lower(),
                drug_class=r.get("drug_class", ""),
                manufacturer=r.get("manufacturer", ""),
                verified=r.get("verified", "").lower() in ("yes", "true", "1"),
                note=r.get("note", ""),
                source_file=name,
            )
    return out


@lru_cache(maxsize=1)
def load_rule_tables() -> RuleTables:
    interactions: list[InteractionRow] = []
    for name in ("interactions_seed.csv", "interactions_ddinter.csv"):
        path = DATA_DIR / name
        if path.exists():
            interactions += [
                InteractionRow(r["a"].lower(), r["b"].lower(), r["severity"].lower(), r["effect"], r["source"],
                               r.get("effect_bn", ""))
                for r in _read_csv(path)
            ]
    beers = [BeersRow(r["target"].lower(), r["reason"], r["recommendation"], r.get("reason_bn", ""))
             for r in _read_csv(DATA_DIR / "beers_seed.csv")]
    dup = frozenset(
        line.strip().lower()
        for line in (DATA_DIR / "duplicate_classes.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    return RuleTables(tuple(interactions), tuple(beers), dup)


@lru_cache(maxsize=1)
def load_generics_bn() -> dict[str, str]:
    path = DATA_DIR / "generics_bn.csv"
    return {r["generic"].lower(): r["bn"] for r in _read_csv(path)} if path.exists() else {}


def class_for_generic(generic: str) -> str | None:
    """Drug class of a generic from the brand table (used for web-found brands)."""
    for row in load_brands().values():
        if row.generic == generic.lower() and row.drug_class:
            return row.drug_class
    return None
