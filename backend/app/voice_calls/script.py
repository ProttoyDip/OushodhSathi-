"""The daily check-in call: fixed Bangla prompts and a small state machine. No AI anywhere in a call.

Every prompt is a pre-recorded file in frontend/public/audio/call/<id>.mp3 (recorded or generated
once, then checked by a native speaker; never live TTS). The texts here are the script of record:
generic wording, no names, and nothing that tells anyone to stop, start, change, skip or double a
medicine (tests run them through explain.is_safe). After "2" (not taken) the call says nothing about
it: the answer is only recorded for the pharmacist.
"""
from __future__ import annotations

from dataclasses import dataclass, field

SLOTS = ("morning", "noon", "night")

PROMPTS: dict[str, dict[str, str]] = {
    "greeting": {"bn": "আসসালামু আলাইকুম, ওষুধসাথী থেকে বলছি।",
                 "en": "Assalamu alaikum, this is OushodhSathi."},
    "slot_morning": {"bn": "সকালের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন।",
                     "en": "If the morning medicine was taken, press 1. If not, press 2."},
    "slot_noon": {"bn": "দুপুরের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন।",
                  "en": "If the noon medicine was taken, press 1. If not, press 2."},
    "slot_night": {"bn": "রাতের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন।",
                   "en": "If the night medicine was taken, press 1. If not, press 2."},
    "emergency_ask": {"bn": "বুকে ব্যথা, শ্বাসকষ্ট বা অজ্ঞান হওয়ার মতো সমস্যা হলে ৯ চাপুন।",
                      "en": "For chest pain, breathing trouble or fainting, press 9."},
    "emergency": {"bn": "এখনই ৯৯৯-এ ফোন করুন বা কাছের হাসপাতালে যান।",
                  "en": "Call 999 now or go to the nearest hospital."},
    "closing": {"bn": "ধন্যবাদ। কোনো প্রশ্ন থাকলে ফার্মাসিস্টকে জিজ্ঞেস করুন।",
                "en": "Thank you. If you have any questions, ask the pharmacist."},
}


@dataclass
class Turn:
    """What the call does next: play these prompts, then wait for a key (or hang up)."""
    play: list[str]
    expects_input: bool
    done: bool = False
    record: dict[str, str] = field(default_factory=dict)  # slot -> taken | missed
    emergency: bool = False


def steps_for(slots: list[str]) -> list[str]:
    return [f"slot_{s}" for s in SLOTS if s in slots] + ["emergency_ask"]


def start(steps: list[str]) -> Turn:
    return Turn(play=["greeting", steps[0]], expects_input=True)


def advance(steps: list[str], index: int, digit: str | None, repeated: bool) -> tuple[int, bool, Turn]:
    """-> (next index, next 'repeated' flag, turn). 9 at any prompt is the emergency branch.
    A missing or wrong key repeats the prompt once, then moves on without recording anything."""
    step = steps[index]
    if digit == "9":
        return index, False, Turn(play=["emergency", "closing"], expects_input=False, done=True, emergency=True)
    record: dict[str, str] = {}
    if step.startswith("slot_") and digit in ("1", "2"):
        record[step.removeprefix("slot_")] = "taken" if digit == "1" else "missed"
    elif not repeated:
        return index, True, Turn(play=[step], expects_input=True)
    nxt = index + 1
    if nxt >= len(steps):
        return nxt, False, Turn(play=["closing"], expects_input=False, done=True, record=record)
    return nxt, False, Turn(play=[steps[nxt]], expects_input=True, record=record)
