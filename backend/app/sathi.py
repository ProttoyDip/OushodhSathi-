"""Sathi (সাথী): the in-app helper. Next step, app guide, and a bridge to humans.

Order of a question:
  1. guard: emergency words -> fixed emergency message (no AI)
  2. guard: prompt injection -> fixed redirect (no AI)
  3. guard: medical keywords -> fixed "ask the pharmacist" redirect (no AI)
  4. guide retrieval; weak or unclear matches go to the one-word intent model,
     whose failure counts as MEDICAL
  5. the model rephrases ONLY the retrieved guide entries; its answer passes the
     output guard, else the entry's fixed answer is shown
The model sees the state code, guide entries and the question with the patient's name
removed. It has no tools and writes nothing.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Literal

from pydantic import BaseModel, ValidationError

from . import guard, help_index, prompts
from .explain import is_good_bangla, is_safe
from .llm_router import NoProviderAvailable, Router, parse_json
from .next_step import NextStep

log = logging.getLogger("oushodh.sathi")

# a family is waiting: a model that is slower than this loses to the guide's own answer
ANSWER_BUDGET_S = 8.0

Kind = Literal["answer", "not_in_guide", "medical_redirect", "emergency"]
Lang = Literal["bn", "en"]


class Action(BaseModel):
    label: str
    route: str | None = None
    tel: str | None = None
    question_draft: str | None = None


class SathiReply(BaseModel):
    kind: Kind
    text: str
    guide_ids: list[str] = []
    actions: list[Action] = []
    source: str = "fixed"  # fixed | guide | llm:<provider>/<model>


class ModelAnswer(BaseModel):
    """Typed output the model must return."""

    answer: str
    guide_ids: list[str] = []
    language: Lang = "bn"


def _t(lang: Lang, bn: str, en: str) -> str:
    return bn if lang == "bn" else en


def emergency_reply(lang: Lang) -> SathiReply:
    return SathiReply(kind="emergency", text=_t(lang, guard.EMERGENCY_BN, guard.EMERGENCY_EN),
                      actions=[Action(label=_t(lang, "৯৯৯-এ কল করুন", "Call 999"), tel="999")])


def medical_reply(lang: Lang, pid: int, draft: str | None) -> SathiReply:
    return SathiReply(kind="medical_redirect", text=_t(lang, guard.MEDICAL_BN, guard.MEDICAL_EN),
                      actions=[Action(label=_t(lang, "ফার্মাসিস্টকে জিজ্ঞেস করুন", "Ask the pharmacist"),
                                      route=f"/p/{pid}/questions", question_draft=draft)])


def not_in_guide_reply(lang: Lang, pid: int) -> SathiReply:
    return SathiReply(kind="not_in_guide", text=_t(lang, guard.NOT_IN_GUIDE_BN, guard.NOT_IN_GUIDE_EN),
                      actions=[Action(label=_t(lang, "ফার্মাসিস্টকে জিজ্ঞেস করুন", "Ask the pharmacist"),
                                      route=f"/p/{pid}/questions")])


def _redact(text: str, names: list[str]) -> str:
    for n in names:
        if n and len(n) >= 2:
            text = re.sub(re.escape(n), "রোগী", text, flags=re.IGNORECASE)
    return text


def _guide_answer(hit: help_index.Hit, lang: Lang, pid: int) -> SathiReply:
    e = hit.entry
    return SathiReply(kind="answer", text=e.answer[lang], guide_ids=[e.id], source="guide",
                      actions=[Action(label=_t(lang, "এই পাতায় যান", "Open this screen"), route=e.route_for(pid))])


def classify_question(question: str, router: Router | None,
                      redact: list[str] | None = None) -> tuple[str, list[help_index.Hit]]:
    """-> (EMERGENCY | INJECTION | MEDICAL | APP | OTHER, guide hits). No model unless unclear."""
    if guard.is_emergency(question):
        return "EMERGENCY", []
    if guard.is_injection(question):
        return "INJECTION", []
    if guard.looks_medical(question):
        return "MEDICAL", []
    hits = help_index.search(question)
    top = hits[0].score if hits else 0
    if top >= help_index.STRONG_MATCH:
        return "APP", hits
    intent = guard.classify(_redact(question, redact or []), router)
    return intent, hits


def ask(question: str, lang: Lang, pid: int, router: Router | None, *,
        state: str = "", redact: list[str] | None = None) -> SathiReply:
    question = question.strip()[:500]
    if not question:
        return not_in_guide_reply(lang, pid)
    intent, hits = classify_question(question, router, redact)
    if intent == "EMERGENCY":
        return emergency_reply(lang)
    if intent == "INJECTION":
        return medical_reply(lang, pid, None)
    if intent == "MEDICAL":
        return medical_reply(lang, pid, question)
    hits = [h for h in hits if h.score >= help_index.MATCH_THRESHOLD]
    if intent != "APP" or not hits:
        return not_in_guide_reply(lang, pid)

    fallback = _guide_answer(hits[0], lang, pid)
    if router is None:
        return fallback
    entries_text = "\n\n".join(
        f"[{h.entry.id}]\nQ: {h.entry.question[lang]}\nA: {h.entry.answer[lang]}" for h in hits
    )
    clean_q = _redact(question, redact or [])
    messages = [
        {"role": "system", "content": prompts.load("sathi_bn")},
        {"role": "user", "content": f"App state: {state or 'unknown'}\nReply language: {lang}\n\n"
                                    f"Guide entries:\n{entries_text}\n\nQuestion: {clean_q}"},
    ]
    try:
        result = router.chat("sathi", messages, json_mode=True, budget_s=ANSWER_BUDGET_S)
        parsed = ModelAnswer.model_validate(parse_json(result.text))
    except (NoProviderAvailable, ValueError, ValidationError) as e:
        log.info("sathi answer from the guide (%s)", type(e).__name__)
        return fallback
    text = parsed.answer.strip()
    if text == "NOT_IN_GUIDE":
        # the retrieval matched well enough to be here; the entry itself is a safe answer
        return fallback
    ids = [i for i in parsed.guide_ids if i in {h.entry.id for h in hits}] or [hits[0].entry.id]
    problems = guard.output_problems(text, f"{clean_q}\n{entries_text}")
    if problems or (lang == "bn" and not is_good_bangla(text)) or not is_safe(text):
        log.warning("sathi model answer blocked (%s); using the guide entry", ", ".join(problems) or "language")
        return fallback
    entry = help_index.entries()[ids[0]]
    return SathiReply(kind="answer", text=text, guide_ids=ids, source=f"llm:{result.provider}/{result.model}",
                      actions=[Action(label=_t(lang, "এই পাতায় যান", "Open this screen"), route=entry.route_for(pid))])


_NUMBER = re.compile(r"[0-9০-৯]+")


def phrase_next_step(step: NextStep, lang: Lang, router: Router | None) -> tuple[str, str]:
    """-> (text, how). The model may only reword the fixed line: every number and medicine
    name must come from the step's params, else the fixed line is used."""
    fixed = step.text_bn if lang == "bn" else step.text_en
    if router is None or step.code == "EMERGENCY_ACTIVE":
        return fixed, "fixed"
    params = ", ".join(f"{k}={v}" for k, v in step.params.items()) or "none"
    try:
        result = router.chat("sathi", [
            {"role": "system", "content": prompts.load("sathi_nextstep")},
            {"role": "user", "content": f"State: {step.code}\nParameters: {params}\nFixed sentence: {fixed}\n"
                                        f"Reply language: {lang}"},
        ], temperature=0.3, budget_s=ANSWER_BUDGET_S)
    except NoProviderAvailable:
        return fixed, "fixed"
    text = result.text.strip().strip('"').strip()
    allowed_numbers = {str(v) for v in step.params.values()} | {
        str(v).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")) for v in step.params.values()}
    numbers_ok = all(n in allowed_numbers for n in _NUMBER.findall(text))
    if (not text or len(text) > 220 or not numbers_ok or guard.output_problems(text, f"{fixed} {params}")
            or not is_safe(text) or (lang == "bn" and not is_good_bangla(text))):
        return fixed, "fixed"
    return text, f"llm:{result.provider}/{result.model}"


def timed(fn, *args, **kwargs) -> tuple[SathiReply, int]:
    start = time.perf_counter()
    reply = fn(*args, **kwargs)
    return reply, int((time.perf_counter() - start) * 1000)
