"""Reviewer-only blood-pressure trend (app/stats.bp_trend)."""
from datetime import date, timedelta

from app.stats import bp_trend

from .test_api import TOKEN, make_patient

DEMO = [(168, 98), (164, 96), (159, 94), (162, 97), (150, 92), (146, 90), (142, 88)]  # BUILD_PLAN demo week


def series(values, start=date(2026, 11, 1)):
    return [{"taken_on": (start + timedelta(days=i)).isoformat(), "systolic": s, "diastolic": d}
            for i, (s, d) in enumerate(values)]


def test_demo_week_is_falling_with_an_interval_below_zero():
    t = bp_trend(series(DEMO))
    assert t["status"] == "falling"
    s = t["slope"]["systolic"]
    assert s["ci_low"] < s["per_week"] < s["ci_high"] < 0
    assert t["above_target"] == 7 and t["n"] == 7  # every reading is at or above 140 systolic


def test_noisy_flat_readings_show_no_clear_change():
    t = bp_trend(series([(150, 90), (138, 86), (152, 92), (140, 85), (149, 91), (139, 86)]))
    assert t["status"] == "no_clear_change"


def test_rising_readings():
    t = bp_trend(series([(130, 80), (134, 82), (139, 85), (143, 87), (149, 90)]))
    assert t["status"] == "rising"


def test_too_few_readings_give_no_trend():
    assert bp_trend([])["status"] == "no_readings"
    assert bp_trend(series(DEMO[:3]))["status"] == "too_few"
    same_day = [{"taken_on": "2026-11-01", "systolic": s, "diastolic": d} for s, d in DEMO]
    assert bp_trend(same_day)["status"] == "too_few"


def test_endpoint_is_reviewer_only(client):
    pid = make_patient(client)
    for i, (s, d) in enumerate(DEMO):
        day = (date.today() - timedelta(days=6 - i)).isoformat()
        assert client.post(f"/patients/{pid}/bp", json={"systolic": s, "diastolic": d, "taken_on": day}).status_code == 201
    assert client.get(f"/patients/{pid}/bp-trend").status_code == 401  # family key alone is not enough
    r = client.get(f"/patients/{pid}/bp-trend", headers=TOKEN)
    assert r.status_code == 200 and r.json()["status"] == "falling"
