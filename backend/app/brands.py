"""Bangladeshi brand name -> generic matching: normalise, exact, then strict fuzzy."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from rapidfuzz import fuzz, process

from .tables import BrandRow, load_brands

FUZZY_CUTOFF = 88

_STRENGTH = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:mg|mcg|µg|ug|gm|g|ml|iu|%)?(?=\s|$|/)", re.I)
_FORM_WORDS = {
    "tab", "tabs", "tablet", "tablets", "cap", "caps", "capsule", "capsules", "syrup", "syr",
    "susp", "suspension", "inj", "injection", "drop", "drops", "cream", "gel", "oint",
    "sr", "xr", "er", "mr", "cr", "dr", "dt", "od", "mups",
}
_PUNCT = re.compile(r"[^\w\s]")


@dataclass
class BrandMatch:
    query: str
    normalised: str
    match_method: str  # exact | fuzzy | not_found
    match_score: float | None
    row: BrandRow | None

    @property
    def generic(self) -> str | None:
        return self.row.generic if self.row else None

    @property
    def drug_class(self) -> str | None:
        return self.row.drug_class if self.row else None

    @property
    def source(self) -> str | None:
        return self.row.source_file if self.row else None


def normalise(name: str) -> str:
    s = name.lower()
    s = _STRENGTH.sub(" ", s)
    s = s.replace("/", " ")
    s = _PUNCT.sub(" ", s)
    words = [w for w in s.split() if w not in _FORM_WORDS and not w.isdigit()]
    return " ".join(words)


@lru_cache(maxsize=1)
def _index() -> dict[str, BrandRow]:
    """Normalised brand name -> row, so "Seclo 20 Cap" in a dataset indexes as "seclo"."""
    index: dict[str, BrandRow] = {}
    for row in load_brands().values():
        index[normalise(row.brand)] = row  # later rows (brands_full.csv) override the seed
    return index


def match_brand(name: str) -> BrandMatch:
    """Exact match on the normalised name, else fuzzy (ratio >= 88), else not_found.

    fuzz.ratio compares whole strings, so a combination brand such as "Napa Extra"
    scores ~57 against "Napa" and is never force-matched to it.
    """
    brands = _index()
    norm = normalise(name)
    if not norm:
        return BrandMatch(name, norm, "not_found", None, None)
    if norm in brands:
        return BrandMatch(name, norm, "exact", 100.0, brands[norm])
    best = process.extractOne(norm, brands.keys(), scorer=fuzz.ratio, score_cutoff=FUZZY_CUTOFF)
    if best:
        key, score, _ = best
        return BrandMatch(name, norm, "fuzzy", round(score, 1), brands[key])
    return BrandMatch(name, norm, "not_found", None, None)
