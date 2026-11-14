"""Missed-dose risk pipeline: pure features, the training gates, and no hint without a model."""
import importlib.util
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from app import adherence_risk
from app.adherence_features import FEATURES, household_static, household_weeks, vector, week_start, weekly_counts
from app.models import Patient
from app.triage import household_risk

MONDAY = date(2026, 10, 5)


def ticks(week: int, taken: int, missed: int) -> list[dict]:
    day = (MONDAY + timedelta(days=7 * week)).isoformat()
    return [{"day": day, "status": "taken"}] * taken + [{"day": day, "status": "missed"}] * missed


def test_week_start_and_counts():
    assert week_start(date(2026, 10, 8)) == MONDAY
    assert weekly_counts(ticks(0, 3, 1) + ticks(1, 2, 2)) == {MONDAY: (3, 1), MONDAY + timedelta(days=7): (2, 2)}


def test_static_features():
    items = [{"schedule": ["morning", "noon"], "prescriber": "Dr A"}, {"schedule": ["night"], "prescriber": "dr a"},
             {"schedule": ["noon"], "prescriber": ""}]
    assert household_static(items, 70) == {"medicines": 3, "doses_per_day": 4, "prescribers": 1, "age": 70,
                                           "noon_share": 0.5}


def test_household_weeks_use_the_two_weeks_before_and_label_the_next():
    events = ticks(0, 10, 0) + ticks(1, 6, 4) + ticks(2, 3, 7)
    rows = household_weeks(events, [{"schedule": ["morning"], "prescriber": "x"}], 68)
    assert [r["week"] for r in rows] == [MONDAY.isoformat(), (MONDAY + timedelta(days=7)).isoformat()]
    first, second = rows
    assert first["prev2_adherence"] == 1.0 and first["label"] == 1          # the week after: 6 of 10 = 60%
    assert second["prev2_recorded"] == 20 and second["prev2_adherence"] == 0.8
    assert second["label"] == 1                                              # week after: 3/10 taken
    assert len(vector(first)) == len(FEATURES)


def test_weeks_without_enough_ticks_are_not_labelled():
    assert household_weeks(ticks(0, 10, 0) + ticks(1, 2, 0), [], 70) == []


def _trainer():
    spec = importlib.util.spec_from_file_location("train_adherence_model",
                                                  Path(__file__).resolve().parents[2] / "eval" / "train_adherence_model.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["train_adherence_model"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_trainer_refuses_without_enough_real_households(store, tmp_path, monkeypatch):
    from app.demo_seed import seed_demo

    mod = _trainer()
    monkeypatch.setattr(mod, "RESULTS", tmp_path / "results.json")
    monkeypatch.setattr(mod, "MODEL", tmp_path / "adherence_model.joblib")
    seed_demo(store)  # demo households never count
    status = mod.main(store)
    assert status["status"] == "in_progress" and status["households"] == 0
    assert (tmp_path / "results.json").exists()
    assert not mod.MODEL.exists()  # a refused run never writes a model


def test_no_model_means_no_hint(store):
    adherence_risk._model.cache_clear()
    p = Patient(id=1, name="x", age=70, created_at=datetime(2026, 1, 1))
    assert adherence_risk.followup_suggested(store, p) is None
    reasons = {r["code"] for r in household_risk(p, [], [], {}, followup=None)["reasons"]}
    assert "followup_suggested" not in reasons


def test_hint_is_a_small_ordering_reason_only():
    p = Patient(id=1, name="x", age=70, created_at=datetime(2026, 1, 1))
    r = household_risk(p, [], [], {}, followup=True)
    assert {"code": "followup_suggested", "points": 1, "value": True} in r["reasons"]
