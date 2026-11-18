"""The daily WhatsApp check-in, as a small state machine. Fixed Bangla text, no AI, no advice.

1. Once a day, the approved template (the only paid message) asks about today's medicines with three
   quick-reply buttons: all taken / something was missed / emergency.
2. A tap opens WhatsApp's 24-hour customer service window, so every follow-up is a free service message:
   "some missed" asks about each pharmacist-approved slot in turn (taken / not taken / emergency).
3. "Emergency" at any point sends the fixed 999 message and alerts the family contact.
After "not taken" nothing is said about it: the answer is only recorded for the pharmacist.

Limits from Meta's docs (https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-reply-buttons-messages
and .../templates/components): up to 3 reply buttons, titles <= 20 characters (template quick replies <= 25).
A template quick-reply tap arrives with the button LABEL as its payload, so template buttons are matched by
label; interactive buttons carry the id we set.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..voice_calls.script import SLOTS

TEMPLATE_NAME = "oushodh_daily_checkin"
TEMPLATE_LANGUAGE = "bn"  # Bengali, per .../templates/supported-languages

DAILY = "আসসালামু আলাইকুম, ওষুধসাথী থেকে বলছি। আজকের ওষুধগুলো কি খাওয়া হয়েছে?"
ALL_TAKEN, SOME_MISSED, EMERGENCY = "সব খেয়েছি", "কিছু বাদ গেছে", "জরুরি সমস্যা"
TEMPLATE_BUTTONS = (ALL_TAKEN, SOME_MISSED, EMERGENCY)

SLOT_QUESTION = {"morning": "সকালের ওষুধ কি খাওয়া হয়েছে?", "noon": "দুপুরের ওষুধ কি খাওয়া হয়েছে?",
                 "night": "রাতের ওষুধ কি খাওয়া হয়েছে?"}
TAKEN, MISSED, EMERGENCY_SHORT = "খেয়েছি", "খাইনি", "জরুরি"
SLOT_BUTTONS = (("taken", TAKEN), ("missed", MISSED), ("emergency", EMERGENCY_SHORT))

EMERGENCY_TEXT = "এখনই ৯৯৯-এ ফোন করুন বা কাছের হাসপাতালে যান।"
CLOSING = "ধন্যবাদ। কোনো প্রশ্ন থাকলে ফার্মাসিস্টকে জিজ্ঞেস করুন।"
TAP_PLEASE = "উত্তর দিতে ওপরের বোতামগুলোর একটি চাপুন। প্রশ্ন থাকলে অ্যাপে ফার্মাসিস্টকে জিজ্ঞেস করুন।"

ALL_TEXTS = [DAILY, *TEMPLATE_BUTTONS, *SLOT_QUESTION.values(), TAKEN, MISSED, EMERGENCY_SHORT,
             EMERGENCY_TEXT, CLOSING, TAP_PLEASE]


@dataclass
class Out:
    """One message to send: text, plus reply buttons [(id, title)] (none = plain text)."""
    text: str
    buttons: list[tuple[str, str]] = field(default_factory=list)
    template: bool = False


@dataclass
class Step:
    out: list[Out]
    state: str                       # daily | slot:<name> | done | emergency
    record: dict[str, str] = field(default_factory=dict)
    emergency: bool = False


def start() -> Out:
    return Out(DAILY, [(label, label) for label in TEMPLATE_BUTTONS], template=True)


def _ask(slot: str) -> Out:
    return Out(SLOT_QUESTION[slot], [(f"{slot}:{k}", title) for k, title in SLOT_BUTTONS])


def reply(state: str, slots: list[str], answered: dict[str, str], tapped: str) -> Step:
    """tapped: a template label (daily) or an interactive id "<slot>:<taken|missed|emergency>"."""
    ordered = [s for s in SLOTS if s in slots]
    if tapped in (EMERGENCY, EMERGENCY_SHORT) or tapped.endswith(":emergency"):
        return Step([Out(EMERGENCY_TEXT), Out(CLOSING)], "emergency", emergency=True)
    if state == "daily":
        if tapped == ALL_TAKEN:
            return Step([Out(CLOSING)], "done", record={s: "taken" for s in ordered})
        if tapped == SOME_MISSED and ordered:
            return Step([_ask(ordered[0])], f"slot:{ordered[0]}")
    elif state.startswith("slot:"):
        slot, _, verdict = tapped.partition(":")
        if slot == state[5:] and verdict in ("taken", "missed"):
            left = [s for s in ordered if s != slot and s not in answered]
            if left:
                return Step([_ask(left[0])], f"slot:{left[0]}", record={slot: verdict})
            return Step([Out(CLOSING)], "done", record={slot: verdict})
    return Step([], state)  # a stale or unknown tap: nothing changes
