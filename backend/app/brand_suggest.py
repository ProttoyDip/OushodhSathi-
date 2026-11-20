""""Did you mean?" for a brand the app did not recognise: up to three brands from the table, for the
family to tap if one is what is printed. A suggestion is never applied by itself, never changes a finding,
and the pharmacist still reviews the list.

Two signals, fused by reciprocal rank (as in help_index.fuse):
- spelling: RapidFuzz ratio (whole-string; WRatio over-rewarded partial overlaps) over the normalised brand
  names, cut-off 60 and the same first letter (a typo or a cut-off name: "Napa Extr", "Seclo2"; never an
  unrelated medicine such as "Rupain" -> "Tryptin"), Bangla aliases included;
- meaning across scripts: the embedding model already used for Sathi (app/embeddings.py), which brings
  "নাপা" or "napa ekstra" close to "Napa" / "Napa Extra" where letters alone cannot. Optional: without a
  key or on an embedding error, spelling alone is used.
"""
from __future__ import annotations

import logging

from rapidfuzz import fuzz, process

from . import embeddings
from .brands import _bn_index, _index, has_bangla, normalise, normalise_bn

log = logging.getLogger("oushodh.brand_suggest")

SPELLING_CUTOFF = 60   # a suggestion for a human, not a match; plus the same first letter (below)
GENERIC_CUTOFF = 80    # a query that is a generic name ("losartan") may surface its brands
EMBED_MIN_COSINE = 0.45
RRF_K = 60
_brand_vectors: dict[str, list[float]] = {}


def _names() -> dict[str, str]:
    """Searchable name -> brand: every table brand, plus its Bangla aliases."""
    rows = _index()
    out = {key: row.brand for key, row in rows.items()}
    for bn, brand in _bn_index().items():
        if normalise(brand) in rows:
            out[bn] = rows[normalise(brand)].brand
    return out


def _spelling(query: str, names: dict[str, str], k: int) -> list[str]:
    q = normalise_bn(query) if has_bangla(query) else normalise(query)
    if not q:
        return []
    hits = process.extract(q, list(names), scorer=fuzz.ratio, score_cutoff=SPELLING_CUTOFF, limit=k * 6)
    ranked: list[str] = []
    for key, _, _ in hits:
        if key[:1] != q[:1]:
            continue  # "Rupain" must never suggest "Tryptin": an unrelated medicine is worse than none
        if names[key] not in ranked:
            ranked.append(names[key])
    return ranked


def _meaning(query: str, k: int) -> list[str]:
    if not embeddings.configured():
        return []
    rows = _index()
    # Meaning search covers the curated seed only: embedding all ~14k dataset brands would take hundreds
    # of calls on the first request. Spelling search still covers the full list.
    brands = sorted({row.brand for row in rows.values() if row.source_file == "brands_seed.csv"})
    try:
        missing = [b for b in brands if b not in _brand_vectors]
        if missing:
            texts = [f"{b} ({rows[normalise(b)].generic})" for b in missing]
            for b, v in zip(missing, embeddings.embed(texts, "passage")):
                _brand_vectors[b] = v
        qv = embeddings.embed([query], "query")[0]
    except embeddings.EmbeddingsUnavailable as e:
        log.info("brand suggestions without embeddings (%s)", e)
        return []
    scored = sorted(((embeddings.cosine(qv, _brand_vectors[b]), b) for b in brands), reverse=True)
    return [b for cos, b in scored[:k * 3] if cos >= EMBED_MIN_COSINE and _plausible(query, b, rows)]


def _plausible(query: str, brand: str, rows) -> bool:
    """Meaning alone may not put a medicine in front of a family: the query must also look like the brand
    (same first letter, close spelling), or name the brand's generic, or be in Bangla script (where
    letters cannot be compared and the meaning is the point)."""
    if has_bangla(query):
        return True
    q, b = normalise(query), normalise(brand)
    if q[:1] == b[:1] and fuzz.ratio(q, b) >= SPELLING_CUTOFF:
        return True
    row = rows.get(b)
    generic = (row.generic or "").lower() if row else ""
    return any(fuzz.partial_ratio(q, part.strip()) >= GENERIC_CUTOFF for part in generic.split("+") if part.strip())


def suggest(query: str, k: int = 3) -> list[dict]:
    """-> [{"brand", "generic", "strength"}] best first; [] when nothing is close."""
    query = (query or "").strip()[:80]
    if not query:
        return []
    names = _names()
    lists = [_spelling(query, names, k), _meaning(query, k)]
    score: dict[str, float] = {}
    for ranked in lists:
        for rank, brand in enumerate(ranked, 1):
            score[brand] = score.get(brand, 0.0) + 1 / (RRF_K + rank)
    rows = _index()
    out = []
    for brand in sorted(score, key=lambda b: -score[b])[:k]:
        row = rows[normalise(brand)]
        out.append({"brand": row.brand, "generic": row.generic, "strength": row.strength or None})
    return out
