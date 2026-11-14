"""Reviewer-only "follow-up suggested" hint from the missed-dose risk model.

Returns None (no hint at all) unless a model trained by eval/train_adherence_model.py exists, passed
its data gates, and scikit-learn is installed. Today none exists, so the reviewer sees nothing.
The hint only orders the queue (app/triage.py); it never creates, removes or changes a finding and
is never shown to the family.
"""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from .adherence_features import household_weeks, vector

log = logging.getLogger("oushodh.adherence_risk")

MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "adherence_model.joblib"
RESULTS_PATH = Path(__file__).resolve().parent.parent.parent / "eval" / "adherence_model_results.json"
THRESHOLD = 0.5


@lru_cache(maxsize=1)
def _model():
    if not MODEL_PATH.exists() or not RESULTS_PATH.exists():
        return None
    try:
        if json.loads(RESULTS_PATH.read_text(encoding="utf-8")).get("status") != "done":
            return None
        import joblib  # only present where scikit-learn is installed
        return joblib.load(MODEL_PATH)
    except Exception as e:  # noqa: BLE001 - no model means no hint
        log.info("adherence model not loaded: %s", type(e).__name__)
        return None


def followup_suggested(store, patient) -> bool | None:
    """True when the model expects adherence below 80% next week; None when there is no model."""
    model = _model()
    if model is None or patient.is_demo:
        return None
    items = [it.model_dump() for it in store.list_items(patient.id, confirmed_only=True)
             if it.schedule and it.schedule_approved_at and not it.stopped and not it.set_aside]
    events = store.list_doses(patient.id, since=(date.today() - timedelta(days=28)).isoformat())
    # the newest complete feature row: pretend "next week" is labelled so the row is produced
    rows = household_weeks(events + [{"day": (date.today() + timedelta(days=7)).isoformat(), "status": "taken"}] * 5,
                           items, patient.age)
    if not rows:
        return None
    try:
        return bool(model.predict_proba([vector(rows[-1])])[0][1] >= THRESHOLD)
    except Exception:  # noqa: BLE001
        return None
