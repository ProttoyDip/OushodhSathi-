"""Bangla explanations for CONFIRMED flags only.

The LLM only rewords a finding the rules engine produced and a clinician confirmed.
Output is post-checked; anything that looks like dosing or an instruction to stop a
medicine is rejected in favour of a fixed template.
"""
from __future__ import annotations

import logging
import re

from . import prompts
from .llm_router import NoProviderAvailable, Router
from .models import MedicineItem, StoredFlag
from .tables import load_generics_bn

log = logging.getLogger("oushodh.explain")

SAFETY_SENTENCE = "ডাক্তারের সাথে কথা না বলে কোনো ওষুধ বন্ধ বা পরিবর্তন করবেন না।"

# digits (Latin or Bangla) followed by a dose unit/count, or stop/skip instructions
_DOSE = re.compile(r"[0-9০-৯]+(?:[.,][0-9০-৯]+)?\s*(?:mg|ml|mcg|মিগ্রা|মিলিগ্রাম|মিলি|টি|টা|বার)", re.I)
_FORBIDDEN = ("বন্ধ করুন", "খাওয়া বাদ দিন", "খাবেন না", "বাদ দিন", "শুরু করুন", "বাড়িয়ে দিন", "কমিয়ে দিন")


def is_safe(text: str) -> bool:
    body = text.replace(SAFETY_SENTENCE, "")
    if _DOSE.search(body):
        return False
    return not any(w in body for w in _FORBIDDEN)


def with_safety_sentence(text: str) -> str:
    text = text.strip()
    if not text.endswith(SAFETY_SENTENCE):
        text = text.replace(SAFETY_SENTENCE, "").strip()
        text = f"{text} {SAFETY_SENTENCE}".strip()
    return text


def generic_bn(generic: str | None) -> str:
    if not generic:
        return "একই ওষুধ"
    parts = [load_generics_bn().get(g.strip().lower(), g.strip()) for g in generic.split("+")]
    return " + ".join(parts)


def _brands(items: list[MedicineItem]) -> str:
    names = [it.brand for it in items]
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " ও " + names[-1]


def template(flag: StoredFlag, items: list[MedicineItem]) -> str:
    """Fixed, pre-reviewed Bangla text per flag code. Contains no doses or instructions."""
    brands = _brands(items)
    reviewer = "ডাক্তার" if flag.routed_to == "doctor" else "ফার্মাসিস্ট"
    m = flag.meta
    if flag.code == "DUPLICATE_GENERIC":
        text = (f"{brands} — নাম আলাদা হলেও দুটোই আসলে একই ওষুধ: {generic_bn(m.get('generic'))}। "
                f"একসাথে খেলে একই ওষুধ দুইবার খাওয়া হতে পারে। {reviewer} বিষয়টি দেখেছেন।")
    elif flag.code == "THERAPEUTIC_DUPLICATION":
        text = (f"{brands} একই ধরনের ওষুধ; সাধারণত এর একটিই যথেষ্ট। "
                f"{reviewer} বিষয়টি দেখেছেন।")
    elif flag.code == "INTERACTION":
        effect = m.get("effect_bn") or "একটি আরেকটির কাজে প্রভাব ফেলতে পারে।"
        text = f"{brands} একসাথে খেলে সমস্যা হতে পারে: {effect} {reviewer} বিষয়টি দেখেছেন।"
    elif flag.code == "BEERS_65":
        reason = m.get("reason_bn") or ""
        text = (f"{brands} বয়স্কদের জন্য সাবধানে ব্যবহারের ওষুধের তালিকায় আছে। {reason} "
                f"{reviewer} বিষয়টি দেখেছেন।")
    elif flag.code == "EXPIRED":
        if flag.severity == "red":
            text = f"{brands} ওষুধটির মেয়াদ শেষ হয়ে গেছে। {reviewer} বিষয়টি দেখেছেন।"
        else:
            text = f"{brands} ওষুধটির মেয়াদ শীঘ্রই শেষ হবে। {reviewer} বিষয়টি দেখেছেন।"
    else:
        text = f"{reviewer} একটি বিষয় দেখেছেন।"
    return with_safety_sentence(" ".join(text.split()))


def _redact(text: str, names: list[str]) -> str:
    for n in names:
        if n:
            text = text.replace(n, "রোগী")
    return text


def explain_flag(flag: StoredFlag, items: list[MedicineItem], note: str | None,
                 router: Router | None, redact: list[str] | None = None) -> tuple[str, str]:
    """Returns (bangla_text, how) where how is "llm:<provider>/<model>" or "template".

    Only medicine names, generics and the finding are sent to the model; patient
    names in the reviewer's note are redacted first (AGENTS.md rule 5).
    """
    if flag.status != "confirmed":
        raise ValueError("explanations are only written for confirmed flags")
    fallback = template(flag, items)
    if router is None:
        return fallback, "template"
    finding = "\n".join([
        f"Finding: {flag.code} ({flag.severity})",
        "Medicines: " + "; ".join(f"{it.brand} = {it.generic or 'unknown'}" for it in items),
        f"Evidence: {flag.evidence}",
        f"Reviewed by: {flag.routed_to}",
        f"Note from the reviewer: {_redact(note or '', redact or []) or '(none)'}",
    ])
    messages = [
        {"role": "system", "content": prompts.load("explain_bn")},
        {"role": "user", "content": finding},
    ]
    try:
        result = router.chat("explain_bn", messages, temperature=0.2)
    except NoProviderAvailable as e:
        log.info("explanation via template (%s)", e)
        return fallback, "template"
    text = result.text.strip().strip('"')
    if not text or not is_safe(text):
        log.warning("explanation from %s rejected by post-check; using template", result.provider)
        return fallback, "template"
    return with_safety_sentence(text), f"llm:{result.provider}/{result.model}"
