"""Taken / missed ticks, reviewer adherence with Wilson intervals, triage and next step."""
from datetime import date, timedelta

import pytest

from app.next_step import StepContext, next_step
from app.stats import wilson
from app.triage import household_risk

TOKEN = {"X-Reviewer-Token": "test-token"}


def home(client, approve=True):
    r = client.post("/patients", json={"name": "Ticks Home", "age": 70, "consent": True})
    pid, h = r.json()["id"], {"X-Family-Key": r.json()["family_key"]}
    it = client.post(f"/patients/{pid}/items?confirmed=true",
                     json={"brand": "Camlodin", "schedule": ["morning", "night"]}, headers=h).json()
    if approve:
        client.post(f"/patients/{pid}/schedule/approve", json={}, headers=TOKEN)
    return pid, h, it["id"]


def tick(client, pid, h, item_id, day, slot="morning", status="taken"):
    return client.post(f"/patients/{pid}/doses", headers=h,
                       json={"item_id": item_id, "day": day.isoformat(), "slot": slot, "status": status})


def test_a_second_tap_updates_the_same_dose(client):
    pid, h, item = home(client)
    today = date.today()
    assert tick(client, pid, h, item, today).status_code == 201
    assert tick(client, pid, h, item, today, status="missed").json()["status"] == "missed"
    rows = client.get(f"/patients/{pid}/doses?days=1", headers=h).json()
    assert len(rows) == 1 and rows[0]["status"] == "missed"


def test_day_limits(client, store):
    pid, h, item = home(client)
    store.update_item(item, schedule_approved_at=(date.today() - timedelta(days=30)).isoformat() + "T08:00:00+00:00")
    assert tick(client, pid, h, item, date.today() - timedelta(days=7)).status_code == 201
    assert tick(client, pid, h, item, date.today() - timedelta(days=8)).status_code == 422
    assert tick(client, pid, h, item, date.today() + timedelta(days=3)).status_code == 422


def test_only_approved_scheduled_slots_can_be_ticked(client):
    pid, h, item = home(client, approve=False)
    assert tick(client, pid, h, item, date.today()).status_code == 422  # not approved yet
    client.post(f"/patients/{pid}/schedule/approve", json={}, headers=TOKEN)
    assert tick(client, pid, h, item, date.today(), slot="noon").status_code == 422  # not on the schedule
    other = client.post("/patients", json={"name": "Other", "age": 70, "consent": True}).json()
    assert client.post(f"/patients/{other['id']}/doses", headers={"X-Family-Key": other["family_key"]},
                       json={"item_id": item, "day": date.today().isoformat(), "slot": "morning",
                             "status": "taken"}).status_code == 404  # another household's medicine


def test_ticks_before_the_plan_was_approved_are_refused(client):
    pid, h, item = home(client)
    assert tick(client, pid, h, item, date.today() - timedelta(days=3)).status_code == 422


def test_reviewer_adherence_with_wilson_interval(client, store):
    pid, h, item = home(client)
    store.update_item(item, schedule_approved_at=(date.today() - timedelta(days=30)).isoformat() + "T08:00:00+00:00")
    for i in range(6):
        day = date.today() - timedelta(days=i)
        tick(client, pid, h, item, day, "morning", "taken")
        tick(client, pid, h, item, day, "night", "missed" if i < 2 else "taken")
    assert client.get(f"/patients/{pid}/adherence", headers=h).status_code == 401
    a = client.get(f"/patients/{pid}/adherence", headers=TOKEN).json()
    [m] = a["medicines"]
    assert (m["taken"], m["missed"], m["recorded"]) == (10, 2, 12)
    lo, hi = wilson(10, 12)
    assert m["adherence"]["p"] == pytest.approx(10 / 12, abs=1e-4)
    assert m["adherence"]["ci_low"] == pytest.approx(lo, abs=1e-4) and m["adherence"]["ci_high"] == pytest.approx(hi, abs=1e-4)
    assert m["expected"] == 28  # 14 days x 2 approved slots: 12 of 28 expected doses were recorded


def test_no_family_endpoint_returns_percentages(client):
    pid, h, item = home(client)
    tick(client, pid, h, item, date.today())
    for path in ("/doses?days=7", "/today", "/report", "/status", ""):
        body = str(client.get(f"/patients/{pid}{path}", headers=h).json())
        assert "adherence" not in body and "ci_low" not in body, path


def test_triage_adds_adherence_low():
    from datetime import datetime

    from app.models import Patient

    p = Patient(id=1, name="x", age=60, created_at=datetime(2026, 1, 1))
    reasons = lambda r: {x["code"]: x for x in r["reasons"]}  # noqa: E731
    assert "adherence_low" in reasons(household_risk(p, [], [], {}, adherence=(7, 5)))
    assert reasons(household_risk(p, [], [], {}, adherence=(7, 5)))["adherence_low"]["points"] == 2
    assert "adherence_low" not in reasons(household_risk(p, [], [], {}, adherence=(5, 3)))   # under 10 recorded
    assert "adherence_low" not in reasons(household_risk(p, [], [], {}, adherence=(9, 1)))   # 90%
    assert "adherence_low" not in reasons(household_risk(p, [], [], {}))                     # no data


def test_export_and_delete_include_ticks(client, store):
    pid, h, item = home(client)
    tick(client, pid, h, item, date.today())
    assert client.get(f"/patients/{pid}/export", headers=h).json()["dose_ticks"][0]["status"] == "taken"
    client.request("DELETE", f"/patients/{pid}", headers=h, json={"confirm": "DELETE"})
    assert store._all("SELECT * FROM dose_events WHERE patient_id = ?", (pid,)) == []


def test_deleting_a_medicine_removes_its_ticks(client, store):
    pid, h, item = home(client)
    tick(client, pid, h, item, date.today())
    assert client.delete(f"/items/{item}", headers=h).status_code == 204
    assert store._all("SELECT * FROM dose_events WHERE item_id = ?", (item,)) == []


def test_next_step_suggests_ticking_and_never_advises_a_dose():
    step = next_step(StepContext(any_items=True, reviewed=True, passport_seen=True, doses_unticked_today=2), 7)
    assert step.code == "TICK_TODAY" and step.route == "/p/7/today"
    for text in (step.text_bn, step.text_en):
        assert "দুইবার" not in text and "double" not in text.lower() and "take it now" not in text.lower()
    assert next_step(StepContext(any_items=True, reviewed=True, passport_seen=True), 7).code == "ALL_GOOD"


def test_next_step_counts_unticked_doses(client):
    pid, h, item = home(client)
    client.post(f"/patients/{pid}/check", headers=h)
    client.post(f"/patients/{pid}/seen", json={"what": "results"}, headers=h)
    client.post(f"/patients/{pid}/seen", json={"what": "passport"}, headers=h)
    step = client.get(f"/patients/{pid}/next-step?lang=en", headers=h).json()
    assert step["code"] == "TICK_TODAY" and step["params"]["n"] == 2
    tick(client, pid, h, item, date.today(), "morning")
    tick(client, pid, h, item, date.today(), "night", "missed")
    assert client.get(f"/patients/{pid}/next-step?lang=en", headers=h).json()["code"] == "ALL_GOOD"
