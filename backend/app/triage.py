"""Reviewer queue priority: which household should a pharmacist look at first?

Deterministic and explainable (no AI). It never creates, removes or changes a flag;
it only orders the queue. Every point comes with a reason the reviewer can read.
"""
from __future__ import annotations

from collections.abc import Iterable

from .models import MedicineItem, Patient, StoredFlag

POLYPHARMACY = 5        # five or more regular medicines
HEAVY_POLYPHARMACY = 10


ADHERENCE_LOW = 0.80        # 14-day share of recorded doses marked taken
ADHERENCE_MIN_RECORDED = 10  # ...counted only with at least this many recorded doses


def household_risk(patient: Patient, items: Iterable[MedicineItem], pending: Iterable[StoredFlag],
                   acb: dict[str, int], adherence: tuple[int, int] | None = None) -> dict:
    """adherence: (taken, missed) over the last 14 days, from the family's ticks."""
    """Return {"score": int, "reasons": [{"code": str, "points": int, "value": ...}]}."""
    items = [it for it in items if not getattr(it, "stopped", False)]
    pending = list(pending)
    reasons: list[dict] = []

    def add(code: str, points: int, value) -> None:
        if points:
            reasons.append({"code": code, "points": points, "value": value})

    reds = sum(f.severity == "red" for f in pending)
    ambers = sum(f.severity == "amber" for f in pending)
    add("open_red", 3 * reds, reds)
    add("open_amber", ambers, ambers)

    age = patient.age or 0
    add("age", 2 if age >= 75 else 1 if age >= 65 else 0, age)

    n = len(items)
    add("medicines", 3 if n >= HEAVY_POLYPHARMACY else 2 if n >= POLYPHARMACY else 0, n)

    prescribers = {(it.prescriber or "").strip().lower() for it in items if (it.prescriber or "").strip()}
    add("prescribers", 2 if len(prescribers) >= 3 else 1 if len(prescribers) == 2 else 0, len(prescribers))

    generics = {g.strip().lower() for it in items for g in (it.generic or "").split("+") if g.strip()}
    burden = sum(acb.get(g, 0) for g in generics)
    add("acb", 2 if burden >= 3 else 0, burden)

    if adherence is not None:
        taken, missed = adherence
        recorded = taken + missed
        if recorded >= ADHERENCE_MIN_RECORDED and taken / recorded < ADHERENCE_LOW:
            add("adherence_low", 2, round(taken / recorded, 2))

    return {"score": sum(r["points"] for r in reasons), "reasons": reasons}
