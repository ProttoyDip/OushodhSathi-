""""Did you mean?" for a brand the app did not recognise: up to three brands from the table, for the
family to tap if one is what is printed. A suggestion is never applied by itself, never changes a finding,
and the pharmacist still reviews the list.

Two signals, fused by reciprocal rank (as in help_index.fuse):
- spelling: RapidFuzz ratio (whole-string; WRatio over-rewarded partial overlaps) over the normalised brand names, with a loose cut-off (a typo or a cut-off
  name: "Napa Extr", "Seclo2"), Bangla aliases included;
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

SPELLING_CUTOFF = 55   # loose on purpose: these are suggestions for a human, not matches
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
    hits = process.extract(q, list(names), scorer=fuzz.ratio, score_cutoff=SPELLING_CUTOFF, limit=k * 3)
    ranked: list[str] = []
    for key, _, _ in hits:
        if names[key] not in ranked:
            ranked.append(names[key])
    return ranked


def _meaning(query: str, k: int) -> list[str]:
    if not embeddings.configured():
        return []
    rows = _index()
    brands = sorted({row.brand for row in rows.values()})
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
    return [b for cos, b in scored[:k * 3] if cos >= EMBED_MIN_COSINE]


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
