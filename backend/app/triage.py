"""Reviewer queue priority: which household should a pharmacist look at first?

Deterministic and explainable (no AI). It never creates, removes or changes a flag;
it only orders the queue. Every point comes with a reason the reviewer can read.
"""
from __future__ import annotations

from collections.abc import Iterable

from .models import MedicineItem, Patient, StoredFlag

POLYPHARMACY = 5        # five or more regular medicines
HEAVY_POLYPHARMACY = 10


def household_risk(patient: Patient, items: Iterable[MedicineItem], pending: Iterable[StoredFlag],
                   acb: dict[str, int]) -> dict:
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

    return {"score": sum(r["points"] for r in reasons), "reasons": reasons}
