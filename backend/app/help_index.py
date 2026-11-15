"""Sathi's app guide: docs/help/help_bn.md + help_en.md, and HYBRID retrieval over it.

Each entry has the same id in both files. The keyword scorer normalises Bangla, Banglish and
English, scores every entry with RapidFuzz over its questions and phrasings (both languages) and
adds small keyword boosts. The vector scorer (app/help_vectors.py: contextual chunks embedded with
nvidia/nemotron-3.5-embed-1b) ranks entries by cosine similarity. The two rankings are fused with
Reciprocal Rank Fusion (Cormack, Clarke and Buettcher, SIGIR 2009; k = 60).

Thresholds keep their meaning: a hit counts as "in the guide" when its keyword score reaches
MATCH_THRESHOLD, or when its vector similarity reaches VECTOR_ACCEPT (then it is given exactly
MATCH_THRESHOLD, never STRONG_MATCH, so the intent check still runs). Below that the answer is
NOT_IN_GUIDE and no model is called. Without embeddings the result is exactly the keyword search.
guard.py runs BEFORE any of this: medical and emergency questions never reach retrieval.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz

HELP_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "help"

MATCH_THRESHOLD = 60   # below: not in the guide
STRONG_MATCH = 78      # at or above: clearly an app question, no intent model needed
RRF_K = 60             # Reciprocal Rank Fusion constant (Cormack et al., 2009)
# cosine similarity at which the vector side alone may say "this is in the guide"; set from
# eval/run_retrieval_eval.py (see eval/help_retrieval_results.json), overridable for tuning
VECTOR_ACCEPT = float(os.getenv("HELP_VECTOR_ACCEPT", "0.50"))


@dataclass(frozen=True)
class Entry:
    id: str
    group: dict[str, str]
    question: dict[str, str]
    answer: dict[str, str]
    phrasings: tuple[str, ...]
    route: str

    def route_for(self, pid: int) -> str:
        return self.route.replace("{home}", f"/p/{pid}").replace("{id}", str(pid))


@dataclass(frozen=True)
class Hit:
    entry: Entry
    score: float                  # keyword score 0-100 (raised to MATCH_THRESHOLD by a strong vector match)
    cosine: float | None = None   # vector similarity, when embeddings were used
    fused: float = 0.0            # RRF score that ordered the hits
    agreed: bool = False          # keyword rank 1 and vector rank 1 are this same entry


def _parse(path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = out.setdefault(line[3:].strip(), {})
        elif current is not None and ":" in line and not line.startswith(">"):
            key, _, value = line.partition(":")
            if key.strip() in ("group", "question", "phrasings", "route", "answer"):
                current[key.strip()] = value.strip()
    return out


@lru_cache(maxsize=1)
def entries() -> dict[str, Entry]:
    bn, en = _parse(HELP_DIR / "help_bn.md"), _parse(HELP_DIR / "help_en.md")
    if bn.keys() != en.keys():
        raise ValueError(f"help guide ids differ: {sorted(bn.keys() ^ en.keys())}")
    out = {}
    for id_ in bn:
        b, e = bn[id_], en[id_]
        phrasings = tuple(p.strip() for src in (b, e) for p in src.get("phrasings", "").split("|") if p.strip())
        out[id_] = Entry(
            id=id_,
            group={"bn": b["group"], "en": e["group"]},
            question={"bn": b["question"], "en": e["question"]},
            answer={"bn": b["answer"], "en": e["answer"]},
            phrasings=phrasings,
            route=b.get("route") or e.get("route") or "{home}",
        )
    return out


_PUNCT = re.compile(r"[^\w\s]|_", re.UNICODE)
# Bangla words that carry no meaning for matching (question words, particles, politeness)
_STOP = {
    "কী", "কি", "কীভাবে", "কিভাবে", "কেন", "কখন", "কোথায়", "আমি", "আমার", "আমাদের", "আপনি", "আপনার",
    "করব", "করবো", "করি", "করে", "করুন", "হবে", "হয়", "যায়", "যাবে", "এটা", "এই", "ও", "আর", "না", "তো",
    "how", "do", "i", "what", "the", "a", "an", "is", "to", "my", "can", "does", "it", "of", "on", "in",
    "ki", "kivabe", "keno", "ami", "amar", "korbo", "kori", "hobe", "ta", "na", "er", "e",
}
# A few strong words that pin an entry, in all three ways people write
_KEYWORDS: dict[str, tuple[str, ...]] = {
    "scan.blurry": ("ঝাপসা", "jhapsha", "jhapsa", "blur", "blurry", "focus"),
    "scan.cut-strip": ("কাটা", "kata", "cut", "half", "অর্ধেক", "ordhek"),
    "scan.prescription": ("প্রেসক্রিপশন", "prescription", "হাতের লেখা", "handwritten"),
    "scan.manual": ("হাতে লিখে", "manually", "by hand", "type"),
    "check.web": ("ওয়েব", "web", "internet", "ইন্টারনেট"),
    "check.please-check": ("দাগ", "dashed", "যাচাই করুন", "dotted"),
    "results.colors": ("লাল", "কমলা", "lal", "komola", "red", "amber", "orange", "colour", "color", "রং"),
    "passport.print": ("প্রিন্ট", "print"),
    "passport.whatsapp": ("হোয়াটসঅ্যাপ", "whatsapp", "pdf"),
    "passport.emergency": ("কিউআর", "qr"),
    "refill.how": ("ফুরিয়ে", "শেষ হওয়া", "refill", "running out", "sesh"),
    "bp.add": ("রক্তচাপ", "প্রেসার লিখ", "bp", "blood pressure", "pressure likh", "pressure add"),
    "access.language": ("ভাষা", "english", "ইংরেজি", "bhasha", "language", "bangla"),
    "access.text-size": ("বড় লেখা", "লেখা ছোট", "bigger", "text size", "read aloud", "শুনব", "পড়ে শোনাও"),
    "privacy.delete": ("মুছ", "delete", "erase", "remove my"),
    "share.family": ("শেয়ার", "share", "লিংক", "link", "ভাই", "বোন", "brother", "sister"),
    "review.how-long": ("কত সময়", "কতক্ষণ", "how long", "koto din", "koto shomoy"),
    "start.add-member": ("নতুন রোগী", "add a family", "add my", "notun manush", "আরেকজন"),
}


def _keyword_hit(entry_id: str, raw: str) -> bool:
    for word in _KEYWORDS.get(entry_id, ()):
        if word.isascii():
            if re.search(rf"\b{re.escape(word)}\b", raw):
                return True
        elif word in raw:
            return True
    return False


def normalise(text: str) -> str:
    s = text.lower().replace("ো", "ো").replace("ৌ", "ৌ")
    s = _PUNCT.sub(" ", s)
    return " ".join(w for w in s.split() if w not in _STOP)


@lru_cache(maxsize=1)
def _corpus() -> list[tuple[Entry, tuple[str, ...]]]:
    return [(e, tuple(normalise(t) for t in (e.question["bn"], e.question["en"], *e.phrasings)))
            for e in entries().values()]


def keyword_search(question: str) -> list[Hit]:
    """Every entry scored by RapidFuzz + keyword boosts, best first."""
    q = normalise(question)
    raw = question.lower()
    if not q:
        return []
    hits = []
    for entry, texts in _corpus():
        best = max((0.6 * fuzz.token_set_ratio(q, t) + 0.4 * fuzz.ratio(q, t)) for t in texts if t)
        if _keyword_hit(entry.id, raw):
            best += 12
        hits.append(Hit(entry, round(min(best, 100.0), 1)))
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits


def fuse(keyword: list[Hit], vector: list[tuple[str, float]], k: int = 3) -> list[Hit]:
    """Reciprocal Rank Fusion of the keyword ranking and the vector ranking."""
    cos = dict(vector)
    rrf: dict[str, float] = {}
    for rank, h in enumerate(keyword, 1):
        rrf[h.entry.id] = rrf.get(h.entry.id, 0.0) + 1 / (RRF_K + rank)
    for rank, (id_, _) in enumerate(vector, 1):
        rrf[id_] = rrf.get(id_, 0.0) + 1 / (RRF_K + rank)
    agreed_id = keyword[0].entry.id if vector and keyword and vector[0][0] == keyword[0].entry.id else None
    out = []
    for h in keyword:
        c = cos.get(h.entry.id)
        score = h.score
        if c is not None and c >= VECTOR_ACCEPT and score < MATCH_THRESHOLD:
            score = float(MATCH_THRESHOLD)
        out.append(Hit(h.entry, score, c, round(rrf.get(h.entry.id, 0.0), 6), h.entry.id == agreed_id))
    out.sort(key=lambda h: h.fused, reverse=True)
    return out[:k]


def search(question: str, k: int = 3, vector_text: str | None = None, use_vectors: bool = True) -> list[Hit]:
    """Hybrid search. vector_text: the text to embed (the caller passes it with patient names
    removed). With no embeddings available this is exactly the keyword search."""
    keyword = keyword_search(question)
    if not keyword:
        return []
    vector: list[tuple[str, float]] = []
    if use_vectors:
        from . import help_vectors  # local import: help_vectors imports this module
        vector = help_vectors.search(vector_text or question, k=10)
    if not vector:
        return keyword[:k]
    return fuse(keyword, vector, k)
