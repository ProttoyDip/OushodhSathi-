"""Features for the missed-dose risk model: one row per household-week, from the family's ticks.

Pure functions (no I/O, no AI). The model trained on these (eval/train_adherence_model.py) may only
suggest an ORDER for the reviewer's queue; it never creates, removes or changes a finding and is never
shown to the family. Rows come from real households only: demo households are excluded by the caller.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

LOW_ADHERENCE = 0.80       # the label: next week's adherence below this
MIN_RECORDED_FOR_LABEL = 5  # a week needs at least this many ticks to count as labelled

FEATURES = ("prev2_adherence", "prev2_recorded", "medicines", "doses_per_day", "prescribers", "age", "noon_share")


def week_start(d: date) -> date:
    """Monday of the ISO week."""
    return d - timedelta(days=d.weekday())


def weekly_counts(events: list[dict]) -> dict[date, tuple[int, int]]:
    """{week start: (taken, missed)} from dose_events rows ({"day": "YYYY-MM-DD", "status": ...})."""
    out: dict[date, list[int]] = defaultdict(lambda: [0, 0])
    for e in events:
        w = week_start(date.fromisoformat(str(e["day"])[:10]))
        out[w][0 if e["status"] == "taken" else 1] += 1
    return {w: (t, m) for w, (t, m) in out.items()}


def household_static(items: list[dict], age: int | None) -> dict:
    """Features that describe the medicine list (items: approved, current medicines)."""
    slots = [s for it in items for s in it.get("schedule") or []]
    prescribers = {(it.get("prescriber") or "").strip().lower() for it in items if (it.get("prescriber") or "").strip()}
    return {
        "medicines": len(items),
        "doses_per_day": len(slots),
        "prescribers": len(prescribers),
        "age": age if age is not None else -1,
        "noon_share": round(slots.count("noon") / len(slots), 3) if slots else 0.0,
    }


def household_weeks(events: list[dict], items: list[dict], age: int | None) -> list[dict]:
    """One row per week that has a following labelled week: features from the two weeks before,
    label = adherence in the week after is below LOW_ADHERENCE."""
    weeks = weekly_counts(events)
    static = household_static(items, age)
    rows = []
    for w in sorted(weeks):
        nxt = weeks.get(w + timedelta(days=7))
        if not nxt or sum(nxt) < MIN_RECORDED_FOR_LABEL:
            continue
        prev = [weeks.get(w - timedelta(days=7 * k), (0, 0)) for k in (0, 1)]
        taken, missed = sum(p[0] for p in prev), sum(p[1] for p in prev)
        recorded = taken + missed
        rows.append({
            "week": w.isoformat(),
            "prev2_adherence": round(taken / recorded, 3) if recorded else -1.0,
            "prev2_recorded": recorded,
            **static,
            "label": int(nxt[0] / sum(nxt) < LOW_ADHERENCE),
        })
    return rows


def vector(row: dict) -> list[float]:
    return [float(row[f]) for f in FEATURES]
