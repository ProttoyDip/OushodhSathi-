"""Bangladeshi brand name -> generic matching: normalise, exact, then strict fuzzy."""
from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

from rapidfuzz import fuzz, process

from .tables import DATA_DIR, BrandRow, load_brands

FUZZY_CUTOFF = 88
BN_FUZZY_CUTOFF = 85  # Bangla spellings vary more (এ / অ্যা), but stay strict
BN_FUZZY_MIN_LEN = 5  # never fuzzy-match a short or cut-off fragment ("নাপ" is not "নাপা")

_BENGALI = re.compile("[\u0980-\u09FF]")
# Bangla strengths (৫০০ মিগ্রা, 500 mg) and dosage-form words, in Bangla script
_BN_STRENGTH = re.compile("[0-9০-৯]+(?:[.,][0-9০-৯]+)?\\s*(?:মিগ্রা|মিলিগ্রাম|এমজি|মিলি|গ্রাম|mg|ml|g)?", re.I)
_BN_FORM_WORDS = {"ট্যাবলেট", "ট্যাব", "ক্যাপসুল", "ক্যাপ", "সিরাপ", "ইনজেকশন", "ড্রপ", "ক্রিম", "এসআর", "এক্সআর"}

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


def has_bangla(name: str) -> bool:
    return bool(_BENGALI.search(name or ""))


def normalise_bn(name: str) -> str:
    """Bangla-script brand name: NFC, no strengths, no dosage-form words, single spaces.
    (The Latin normaliser cannot be used: regex \\w drops Bangla vowel signs.)"""
    s = unicodedata.normalize("NFC", name)
    s = _BN_STRENGTH.sub(" ", s)
    s = re.sub("[^\u0980-\u09FF\\s]", " ", s)  # keep Bangla letters and signs only
    s = s.replace("।", " ")
    words = [w for w in s.split() if w not in _BN_FORM_WORDS]
    return " ".join(words)


@lru_cache(maxsize=1)
def _bn_index() -> dict[str, str]:
    """Bangla spelling -> English brand name, from data/brands_bn.csv (pharmacist-checked aliases)."""
    path = DATA_DIR / "brands_bn.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {normalise_bn(r["bn"]): r["brand"].strip() for r in csv.DictReader(f) if r.get("bn") and r.get("brand")}


def _match_bangla(name: str) -> BrandMatch:
    """Bangla script (e.g. a handwritten prescription read as "নাপা ৫০০"): alias table,
    exact then strict fuzzy, then the English brand table for the generic."""
    norm = normalise_bn(name)
    aliases = _bn_index()
    if not norm or not aliases:
        return BrandMatch(name, norm, "not_found", None, None)
    method, score, brand = "exact", 100.0, aliases.get(norm)
    if brand is None:
        long_enough = [a for a in aliases if len(a) >= BN_FUZZY_MIN_LEN]
        best = (process.extractOne(norm, long_enough, scorer=fuzz.ratio, score_cutoff=BN_FUZZY_CUTOFF)
                if len(norm) >= BN_FUZZY_MIN_LEN else None)
        if not best:
            return BrandMatch(name, norm, "not_found", None, None)
        method, score, brand = "fuzzy", round(best[1], 1), aliases[best[0]]
    row = _index().get(normalise(brand))
    if row is None:
        return BrandMatch(name, norm, "not_found", None, None)
    return BrandMatch(name, norm, method, score, row)


@lru_cache(maxsize=1)
def _index() -> dict[str, BrandRow]:
    """Normalised brand name -> row, so "Seclo 20 Cap" in a dataset indexes as "seclo"."""
    index: dict[str, BrandRow] = {}
    for row in load_brands().values():
        key = normalise(row.brand)
        if key in index and index[key].source_file == "brands_seed.csv":
            continue  # the curated seed row wins over any dataset spelling ("Seclo 20 Cap")
        index[key] = row
    return index


def match_brand(name: str) -> BrandMatch:
    """Exact match on the normalised name, else fuzzy (ratio >= 88), else not_found.

    fuzz.ratio compares whole strings, so a combination brand such as "Napa Extra"
    scores ~57 against "Napa" and is never force-matched to it.
    """
    if has_bangla(name):
        return _match_bangla(name)
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
