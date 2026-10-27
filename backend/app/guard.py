"""Sathi's guard. Every message passes it BEFORE a model sees it; every model answer
passes it AFTER. The guard can only make Sathi safer, never less safe.

Step A  emergency words (Bangla, Banglish, English)  -> fixed message, no AI
        prompt-injection attempts                     -> fixed redirect, no AI
Step B  medical intent: keyword patterns first; when a question is neither clearly
        medical nor clearly about the app, a one-word classifier decides, and any
        failure or doubt counts as MEDICAL (fail safe)
Step C  output check on every model answer: doses, stop/start/change instructions,
        medicine names that were not in the input, diagnoses -> blocked
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Literal

from .explain import _DOSE, _FORBIDDEN
from .llm_router import NoProviderAvailable, Router
from .tables import load_brands, load_generics_bn

Intent = Literal["APP", "MEDICAL", "EMERGENCY", "OTHER"]

EMERGENCY_BN = "এটা জরুরি হতে পারে। এখনই কাছের হাসপাতালে যান বা ৯৯৯-এ কল করুন।"
EMERGENCY_EN = "This may be an emergency. Go to the nearest hospital now or call 999."
MEDICAL_BN = "এই প্রশ্নের উত্তর ফার্মাসিস্ট বা ডাক্তার দেবেন। আমি আপনার প্রশ্নটা তাঁদের কাছে পাঠাতে পারি।"
MEDICAL_EN = "A pharmacist or doctor will answer this question. I can send your question to them."
NOT_IN_GUIDE_BN = "এটা আমি জানি না। অ্যাপ নিয়ে অন্য কিছু জিজ্ঞেস করুন, অথবা ফার্মাসিস্টকে প্রশ্ন পাঠান।"
NOT_IN_GUIDE_EN = "I don't know that one. Ask me something else about the app, or send your question to the pharmacist."


def _any(patterns: tuple[str, ...]):
    """Latin words match on word boundaries; Bangla matches as text (it inflects by suffix)."""
    parts = [rf"\b{re.escape(p)}\b" if p.isascii() else re.escape(p) for p in patterns]
    return re.compile("|".join(parts), re.IGNORECASE)


_EMERGENCY = _any((
    # Bangla
    "বুকে ব্যথা", "বুক ব্যথা", "বুকে চাপ", "শ্বাস নিতে কষ্ট", "শ্বাস নিতে পারছে না", "শ্বাস নিতে পারছি না",
    "শ্বাসকষ্ট", "নিঃশ্বাস বন্ধ", "অজ্ঞান", "জ্ঞান হারি", "সাড়া দিচ্ছে না", "এক পাশ অবশ", "অবশ হয়ে",
    "কথা জড়িয়ে", "মুখ বেঁকে", "খিঁচুনি", "রক্ত বমি", "কাশির সাথে রক্ত", "স্ট্রোক", "হার্ট অ্যাটাক",
    "অনেকগুলো ওষুধ খেয়ে", "বেশি ওষুধ খেয়ে", "সব ওষুধ একসাথে খেয়ে", "বিষ খেয়ে",
    # Banglish
    "buke betha", "buke batha", "buk betha", "khub betha", "sash nite parchi na", "shash nite parche na",
    "sash nite parche na", "shash nite kosto", "sash kosto", "oggan", "ojnan", "ogyan", "khichuni",
    "rokto bomi", "beshi oshudh kheye", "onek oshudh kheye", "kotha joriye",
    # English
    "chest pain", "can't breathe", "cannot breathe", "can not breathe", "difficulty breathing",
    "not breathing", "short of breath", "fainted", "unconscious", "passed out", "collapsed", "stroke",
    "seizure", "fitting", "overdose", "took too many", "heart attack", "vomiting blood", "coughing blood",
    "not responding", "face drooping", "slurred speech",
))

_INJECTION = _any((
    "ignore your rules", "ignore the rules", "ignore previous", "ignore all previous", "ignore your instructions",
    "forget your instructions", "forget your rules", "you are now", "act as a doctor", "act as", "pretend to be",
    "pretend you", "system prompt", "developer mode", "jailbreak", "no restrictions", "disregard",
    "নিয়ম ভুলে", "নিয়ম মানতে হবে না", "নিয়ম বাদ দাও", "তুমি এখন ডাক্তার", "ডাক্তার হয়ে উত্তর",
    "tumi ekhon daktar", "niyom vule", "niyom bad", "rules vule",
))

_MEDICAL = _any((
    # dose and schedule
    "কয়টা খাব", "কটা খাব", "কয়টা খাবে", "কতটুকু", "কত মিলি", "ডোজ", "মাত্রা", "কখন খাব", "কখন খাবে",
    "খালি পেটে", "ভরা পেটে", "খাওয়ার আগে", "খাওয়ার পরে", "রাতে খেলে", "সকালে খেলে",
    # stop / start / change / combine
    "বন্ধ করব", "বন্ধ করবো", "বন্ধ করে দেব", "বন্ধ করে দিব", "বন্ধ করা যাবে", "খাওয়া বাদ", "বাদ দেব",
    "বাদ দিব", "খাওয়া ছেড়ে", "একসাথে খাওয়া", "একসাথে খেলে", "একসাথে খাব", "দুটোই খাব", "খেতে পারি",
    "খাওয়া যাবে", "খেলে হবে", "খেলে কি", "খাব কি", "খাবে কি", "বদলে দেব", "ওষুধ বদল", "বিকল্প", "কম খাব",
    "বেশি খাব", "দ্বিগুণ", "খাব", "খাবো", "খাওয়াব", "ওষুধটা কিসের", "ওষুধটি কিসের", "ওষুধ কিসের",
    # symptoms and effects
    "পার্শ্বপ্রতিক্রিয়া", "সাইড ইফেক্ট", "ব্যথা", "জ্বর", "মাথা ঘোর", "বমি", "ডায়রিয়া", "পাতলা পায়খানা",
    "কাশি", "চুলকানি", "ফুলে", "প্রেশার বেশি", "প্রেশার কম", "প্রেশার বেড়ে", "সুগার কম", "সুগার বেশি",
    "সুগার বেড়ে", "দুর্বল", "ঘুম হয় না", "রোজা", "গর্ভ", "অ্যালার্জি হয়েছে",
    # Banglish
    "khabo", "khabe", "khawa jabe", "khete pari", "bondho korbo", "bondho kore", "bad dibo", "bad debo",
    "dutoi", "ekshathe", "eksathe", "dose", "koyta", "kotota", "jor", "betha", "matha ghore", "bomi",
    "pressure beshi", "pressure kom", "sugar kom", "sugar beshi", "roja", "side effect", "khele", "khawabo",
    "oshudh kisher", "oshudhta kisher",
    # English
    "how many tablets", "how many pills", "how much", "dosage", "can i take", "should i take", "should he take",
    "should she take", "safe to take", "stop taking", "start taking", "skip", "double", "together with",
    "instead of", "replace", "side effects", "pain", "fever", "dizzy", "dizziness", "headache", "vomit",
    "diarrh", "rash", "pregnan", "fasting", "interaction", "is it safe", "empty stomach", "before food",
    "after food", "blood sugar", "too high", "too low", "safe for", "medicine for", "tablet for", "pill for",
    "stopped", "missed a dose", "missed dose",
))
# a dose ("2 tablets", "500 mg") or a blood-pressure value to interpret ("140/90")
_DOSE_NUMBER = re.compile(r"[0-9০-৯]+\s*(?:mg|ml|mcg|মিগ্রা|মিলিগ্রাম|মিলি|টা|টি|বার|বেলা)|[0-9০-৯]{2,3}\s*/\s*[0-9০-৯]{2,3}",
                          re.IGNORECASE)


def is_emergency(text: str) -> bool:
    return bool(_EMERGENCY.search(text))


def is_injection(text: str) -> bool:
    return bool(_INJECTION.search(text))


def looks_medical(text: str) -> bool:
    return bool(_MEDICAL.search(text) or _DOSE_NUMBER.search(text))


def classify(question: str, router: Router | None) -> Intent:
    """One-word intent from a tiny model. Any failure or doubt -> MEDICAL (fail safe)."""
    if router is None:
        return "MEDICAL"
    from . import prompts

    try:
        result = router.chat("text", [
            {"role": "system", "content": prompts.load("sathi_intent")},
            {"role": "user", "content": question},
        ])
    except NoProviderAvailable:
        return "MEDICAL"
    word = result.text.strip().strip(".\"'` ").upper()
    return word if word in ("APP", "MEDICAL", "EMERGENCY", "OTHER") else "MEDICAL"  # type: ignore[return-value]


# ---- Step C: output check --------------------------------------------------------------

_STOP_START_EN = _any((
    "stop taking", "start taking", "stop the", "stop it", "start the", "increase", "decrease", "reduce the dose",
    "double the dose", "skip", "switch to", "change the dose", "take it with", "take them together",
))
_DIAGNOSIS = re.compile(
    r"\byou (?:have|might have|may have|are suffering from)\b|\bdiagnos|রোগ হয়েছে|অসুখ হয়েছে|ভুগছেন|রোগে আক্রান্ত",
    re.IGNORECASE,
)
_WORD = re.compile(r"[A-Za-z][A-Za-z\-]{3,}|[ঀ-৿]{3,}")


@lru_cache(maxsize=1)
def _medicine_names() -> frozenset[str]:
    names = set()
    for row in load_brands().values():
        names.add(row.brand.lower())
        names.update(part.strip() for part in row.generic.split("+"))
    for generic, bn in load_generics_bn().items():
        names.add(generic)
        names.add(bn)
    return frozenset(n for n in names if len(n) >= 4)


def medicine_names_in(text: str) -> set[str]:
    words = {w.lower() for w in _WORD.findall(text)}
    return words & _medicine_names()


def output_problems(answer: str, allowed_text: str) -> list[str]:
    """Why a model answer must not be shown. Empty list = safe. `allowed_text` is everything
    the model was given (question, guide entries, step params): names may only come from it."""
    problems = []
    if _DOSE.search(answer) or _DOSE_NUMBER.search(answer):
        problems.append("dose")
    if any(w in answer for w in _FORBIDDEN) or _STOP_START_EN.search(answer):
        problems.append("stop/start/change instruction")
    if extra := medicine_names_in(answer) - medicine_names_in(allowed_text):
        problems.append(f"medicine not in input: {', '.join(sorted(extra))}")
    if _DIAGNOSIS.search(answer):
        problems.append("diagnosis")
    return problems
