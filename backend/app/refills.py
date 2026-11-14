"""Refill rule: how many days a confirmed medicine still lasts. No map, no ordering.

days_left = floor(tablets_left / tablets_per_day), where tablets_per_day =
doses_per_day (times a day, from the schedule) x per_dose (tablets each time).
Only confirmed items that the reviewer has not stopped and the family has not set
aside count: a stopped duplicate must never ask the family to buy more of it.
"""
from __future__ import annotations

import math

from .models import MedicineItem

REFILL_SOON_DAYS = 5


def counts(item: MedicineItem) -> bool:
    """Is this medicine part of what the patient takes now?"""
    return item.confirmed and not item.stopped and not item.set_aside


def days_left(item: MedicineItem) -> int | None:
    if not counts(item) or item.pills_left is None or not item.doses_per_day:
        return None
    per_day = item.doses_per_day * max(item.per_dose, 1)
    return math.floor(item.pills_left / per_day)


def refills_due(items: list[MedicineItem], within: int = REFILL_SOON_DAYS) -> list[tuple[MedicineItem, int]]:
    """Medicines that run out within `within` days, soonest first."""
    due = [(it, d) for it in items if (d := days_left(it)) is not None and d <= within]
    return sorted(due, key=lambda x: (x[1], x[0].brand))
