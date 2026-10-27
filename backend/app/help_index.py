"""Sathi's app guide: docs/help/help_bn.md + help_en.md, and retrieval over it.

Each entry has the same id in both files. Retrieval normalises Bangla, Banglish and
English, scores every entry with RapidFuzz over its questions and phrasings (both
languages), adds small keyword boosts, and returns the best three. Below the threshold
the answer is NOT_IN_GUIDE and no model is called.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz

HELP_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "help"

MATCH_THRESHOLD = 60   # below: not in the guide
STRONG_MATCH = 78      # at or above: clearly an app question, no intent model needed


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
    score: float


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


def search(question: str, k: int = 3) -> list[Hit]:
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
    return hits[:k]
