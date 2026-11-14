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
    # the reference pack a demo price refers to (savings.py); blank when unknown
    strength: str = ""
    form: str = ""
    mrp_bdt: float | None = None  # unit price per tablet, BDT
    pack_source: str = ""

    @property
    def generics(self) -> tuple[str, ...]:
        return tuple(g.strip() for g in self.generic.split("+") if g.strip())


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
class RenalRow:
    """A kidney-dose rule: below this eGFR the medicine needs a clinician's look (renal_seed.csv)."""
    target: str          # a generic, or "class:<drug class>"
    egfr_below: float
    severity: str        # red | amber
    routed_to: str       # doctor | pharmacist
    note: str
    note_bn: str
    source: str


@dataclass(frozen=True)
class RuleTables:
    interactions: tuple[InteractionRow, ...] = ()
    beers: tuple[BeersRow, ...] = ()
    duplicate_classes: frozenset[str] = field(default_factory=frozenset)
    # generic -> Anticholinergic Cognitive Burden score (1-3), from acb_seed.csv
    acb: dict[str, int] = field(default_factory=dict)
    # group ("raas", "diuretic", "nsaid") -> drug classes (lowercase), from class_groups.csv
    class_groups: dict[str, frozenset[str]] = field(default_factory=dict)
    renal: tuple[RenalRow, ...] = ()


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Rows of a CSV file; lines starting with "#" (source and licence notes) are skipped."""
    with path.open(encoding="utf-8", newline="") as f:
        lines = [line for line in f if not line.lstrip().startswith("#")]
    return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(lines)]


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
                strength=(r.get("strength") or "").strip(),
                form=(r.get("form") or "").strip().lower(),
                mrp_bdt=_price(r.get("mrp_bdt")),
                pack_source=(r.get("pack_source") or "").strip(),
            )
    return out


def _price(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


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
    acb_path = DATA_DIR / "acb_seed.csv"
    acb = {r["generic"].lower(): int(r["score"]) for r in _read_csv(acb_path)} if acb_path.exists() else {}
    groups: dict[str, set[str]] = {}
    groups_path = DATA_DIR / "class_groups.csv"
    for r in _read_csv(groups_path) if groups_path.exists() else []:
        groups.setdefault(r["group"].lower(), set()).add(r["drug_class"].lower())
    renal_path = DATA_DIR / "renal_seed.csv"
    renal = tuple(
        RenalRow(r["target"].lower(), float(r["egfr_below"]), r["severity"].lower(), r["routed_to"].lower(),
                 r["note"], r.get("note_bn", ""), r["source"])
        for r in (_read_csv(renal_path) if renal_path.exists() else [])
    )
    return RuleTables(tuple(interactions), tuple(beers), dup, acb,
                      {g: frozenset(c) for g, c in groups.items()}, renal)


@lru_cache(maxsize=1)
def load_generics_bn() -> dict[str, str]:
    path = DATA_DIR / "generics_bn.csv"
    return {r["generic"].lower(): r["bn"] for r in _read_csv(path)} if path.exists() else {}


AWARE_GROUPS = ("Access", "Watch", "Reserve")
AWARE_RANK = {"Access": 0, "Watch": 1, "Reserve": 2}


@lru_cache(maxsize=1)
def load_aware() -> dict[str, str]:
    """Generic (lowercase; combinations as "a + b") -> WHO AWaRe group, from aware_2025.csv.
    WHO AWaRe is CC BY-NC-SA 3.0 IGO (non-commercial): see the file header."""
    path = DATA_DIR / "aware_2025.csv"
    out: dict[str, str] = {}
    for r in _read_csv(path) if path.exists() else []:
        group = r.get("group", "").strip().capitalize()
        if r.get("generic") and group in AWARE_RANK:
            out[" + ".join(g.strip() for g in r["generic"].lower().split("+"))] = group
    return out


def aware_group(generic: str | None) -> str | None:
    """The AWaRe group of a generic. A combination is looked up whole first, then the
    most restricted group of its ingredients wins. None when it is not an antibiotic we know."""
    if not generic:
        return None
    table = load_aware()
    whole = " + ".join(g.strip() for g in generic.lower().split("+") if g.strip())
    if whole in table:
        return table[whole]
    groups = [table[g] for g in whole.split(" + ") if g in table]
    return max(groups, key=AWARE_RANK.__getitem__) if groups else None


def class_for_generic(generic: str) -> str | None:
    """Drug class of a generic from the brand table (used for web-found brands)."""
    for row in load_brands().values():
        if row.generic == generic.lower() and row.drug_class:
            return row.drug_class
    return None
