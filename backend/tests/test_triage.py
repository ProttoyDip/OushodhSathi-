"""Reviewer queue ordering by household risk (app/triage.py)."""
from datetime import datetime

from app.models import MedicineItem, Patient, StoredFlag
from app.tables import load_rule_tables
from app.triage import household_risk

from .test_api import TOKEN, add, make_patient

NOW = datetime(2026, 11, 14)


def patient(age):
    return Patient(id=1, name="x", age=age, created_at=NOW)


def med(i, brand, generic, prescriber=None):
    return MedicineItem(id=i, patient_id=1, brand=brand, generic=generic, prescriber=prescriber, created_at=NOW)


def flag(severity):
    return StoredFlag(id=1, patient_id=1, key="k", code="EXPIRED", severity=severity, item_ids=[1], evidence="e",
                      routed_to="pharmacist", data_source="d", status="pending_review",
                      created_at=NOW, updated_at=NOW)


def test_score_is_explained_point_by_point():
    meds = [med(i, f"B{i}", g, p) for i, (g, p) in enumerate(
        [("amitriptyline", "A"), ("clonazepam", "B"), ("metformin", "C"), ("losartan", "A"), ("amlodipine", "B")], 1)]
    r = household_risk(patient(78), meds, [flag("red"), flag("amber")], load_rule_tables().acb)
    points = {x["code"]: x["points"] for x in r["reasons"]}
    assert points == {"open_red": 3, "open_amber": 1, "age": 2, "medicines": 2, "prescribers": 2, "acb": 2}
    assert r["score"] == sum(points.values()) == 12


def test_quiet_household_scores_zero():
    r = household_risk(patient(50), [med(1, "Comet", "metformin")], [], load_rule_tables().acb)
    assert r == {"score": 0, "reasons": []}


def test_stopped_medicines_do_not_count():
    stopped = med(1, "Tryptin", "amitriptyline").model_copy(update={"stopped": True})
    r = household_risk(patient(50), [stopped], [], load_rule_tables().acb)
    assert r["score"] == 0


def test_queue_puts_the_riskier_household_first_within_amber(client):
    # a quiet 50-year-old household with one amber finding (near-expiry)...
    quiet = make_patient(client, age=50)
    add(client, quiet, "Comet", expiry="2026-12")
    assert client.post(f"/patients/{quiet}/check").status_code == 200
    # ...and a 78-year-old with many medicines from three prescribers and only amber findings
    busy = make_patient(client, age=78)
    for brand, who in (("Seclo", "A"), ("Maxpro", "B"), ("Tryptin", "C"), ("Comet", "A"), ("Atova", "B")):
        add(client, busy, brand, prescriber=who, expiry="2028-01")
    assert client.post(f"/patients/{busy}/check").status_code == 200

    rows = client.get("/flags", headers=TOKEN).json()["flags"]
    ambers = [r for r in rows if r["severity"] == "amber"]
    assert ambers and ambers[0]["patient_id"] == busy
    assert all("priority" in r and r["priority"]["score"] >= 0 for r in rows)
    reds = [i for i, r in enumerate(rows) if r["severity"] == "red"]
    assert not reds or max(reds) < min(i for i, r in enumerate(rows) if r["severity"] == "amber")
