import json
import time

import pytest

from app import clinical
from app.llm_router import NoProviderAvailable, RouterResult
from app.models import MedicineItem, Patient

TOKEN = {"X-Reviewer-Token": "test-token"}


class FakeRouter:
    def __init__(self, text: str | None):
        self.text, self.calls = text, []

    def chat(self, task, messages, **kw):
        self.calls.append((task, messages))
        if self.text is None:
            raise NoProviderAvailable("fake")
        return RouterResult(self.text, "fake", "fake-model")


def household(client, **extra):
    r = client.post("/patients", json={"name": "Clinical Test", "age": 72, **extra})
    client.headers["X-Family-Key"] = r.json()["family_key"]
    return r.json()["id"]


def add(client, pid, brand, **kw):
    r = client.post(f"/patients/{pid}/items?confirmed=true", json={"brand": brand, **kw})
    assert r.status_code == 201, r.text
    return r.json()


# ---- case summary ------------------------------------------------------------------------

PATIENT = Patient(id=1, name="Rahima Begum", age=68, created_at="2026-10-01T00:00:00+00:00")
ITEMS = [MedicineItem(id=1, patient_id=1, brand="Napa", generic="paracetamol", prescriber="Local drug shop"),
         MedicineItem(id=2, patient_id=1, brand="Ace", generic="paracetamol", prescriber="Village doctor")]


def _summary(**kw):
    base = {"summary": ["Two medicines from two prescribers.", "Napa and Ace both contain paracetamol.",
                        "One duplicate finding is pending."],
            "prescribers": [{"name": "Local drug shop", "medicines": ["Napa"]},
                            {"name": "Village doctor", "medicines": ["Ace"]}],
            "questions_to_check": ["Does the village doctor know about the Napa from the shop?"]}
    return json.dumps({**base, **kw})


def test_case_summary_passes_when_it_only_states_facts():
    router = FakeRouter(_summary())
    out = clinical.case_summary(PATIENT, ITEMS, [], router)
    assert out["summary"] and out["dropped"] is None
    sent = json.dumps(router.calls)
    assert "Rahima" not in sent and "68" in sent  # age yes, name never


@pytest.mark.parametrize("bad", [
    {"prescribers": [{"name": "Dr. Somebody Else", "medicines": ["Napa"]}]},
    {"prescribers": [{"name": "Local drug shop", "medicines": ["Seclo"]}]},
    {"summary": ["The patient should stop Ace."]},
    {"summary": ["Napa is 500 mg twice a day."]},
    {"questions_to_check": ["Is Seclo also being taken?"]},
])
def test_case_summary_is_dropped_when_it_invents_or_advises(bad):
    out = clinical.case_summary(PATIENT, ITEMS, [], FakeRouter(_summary(**bad)))
    assert out["summary"] is None and out["dropped"]


def test_case_summary_without_a_model_shows_evidence_only():
    assert clinical.case_summary(PATIENT, ITEMS, [], FakeRouter(None))["summary"] is None


def test_case_summary_endpoint_is_reviewer_only(client):
    pid = household(client)
    assert client.get(f"/patients/{pid}/case-summary").status_code == 401
    r = client.get(f"/patients/{pid}/case-summary?reviewer=Pharm", headers=TOKEN).json()
    assert r["summary"] is None and r["collapsed"] is False


# ---- review time -------------------------------------------------------------------------

def test_review_time_runs_from_opened_to_decided(client):
    pid = household(client)
    add(client, pid, "Napa", prescriber="a")
    add(client, pid, "Ace", prescriber="b")
    client.post(f"/patients/{pid}/check")
    fid = client.get(f"/patients/{pid}/flags?view=reviewer", headers=TOKEN).json()[0]["id"]
    assert client.post(f"/flags/{fid}/opened").status_code == 401
    assert client.post(f"/flags/{fid}/opened", headers=TOKEN).status_code == 204
    client.post(f"/flags/{fid}/review", headers=TOKEN, json={"status": "confirmed", "reviewer": "P", "note": "ok"})
    rt = client.get("/eval/review-time").json()
    assert rt["reviews"] == 1 and rt["median_seconds"] is not None


# ---- blood-pressure photos -----------------------------------------------------------------

def test_bp_photo_reading_is_validated():
    ok = clinical.read_bp_photo(b"x", FakeRouter('{"systolic": 142, "diastolic": 88, "pulse": 72, "confidence": 0.93}'))
    assert ok["readable"] and not ok["needs_check"] and ok["systolic"] == 142
    unsure = clinical.read_bp_photo(b"x", FakeRouter('{"systolic": 142, "diastolic": 88, "confidence": 0.5}'))
    assert unsure["readable"] and unsure["needs_check"]
    for bad in ('{"systolic": 88, "diastolic": 142, "confidence": 0.99}', '{"systolic": 420, "diastolic": 88}',
                "no numbers here"):
        r = clinical.read_bp_photo(b"x", FakeRouter(bad))
        assert not r["readable"] and r["needs_check"] and r["systolic"] is None


def test_bp_keeps_pulse_and_source(client, store):
    pid = household(client)
    r = client.post(f"/patients/{pid}/bp", json={"systolic": 150, "diastolic": 95, "pulse": 80, "source": "photo"})
    assert r.status_code == 201
    row = store._all("SELECT pulse, source FROM bp_readings WHERE patient_id = ?", (pid,))[0]
    assert row == {"pulse": 80, "source": "photo"}


# ---- reviewer-written fields, schedules, set-aside ---------------------------------------

def test_purpose_and_stopped_are_reviewer_only(client):
    pid = household(client)
    item = add(client, pid, "Ace")
    body = {"purpose": "Pain or fever", "purpose_bn": "ব্যথা বা জ্বর", "stopped": True, "reviewer": "Pharm"}
    assert client.patch(f"/items/{item['id']}/clinical", json=body).status_code == 401
    r = client.patch(f"/items/{item['id']}/clinical", json=body, headers=TOKEN).json()
    assert r["purpose_bn"] == "ব্যথা বা জ্বর" and r["stopped"] and r["stopped_by"] == "Pharm"
    # the family cannot write these through the normal item patch
    client.patch(f"/items/{item['id']}", json={"purpose": "x", "stopped": False})
    assert client.get(f"/patients/{pid}/items").json()[0]["stopped"] is True


def test_only_approved_times_reach_todays_medicines(client):
    pid = household(client)
    item = add(client, pid, "Seclo", schedule=["morning"])
    today = client.get(f"/patients/{pid}/today").json()
    assert today["slots"]["morning"] == [] and today["waiting_approval"] == 1
    assert client.post(f"/patients/{pid}/schedule/approve", json={"reviewer": "P"}).status_code == 401
    client.post(f"/patients/{pid}/schedule/approve", json={"reviewer": "P"}, headers=TOKEN)
    assert [m["brand"] for m in client.get(f"/patients/{pid}/today").json()["slots"]["morning"]] == ["Seclo"]
    # changing the times needs the pharmacist again
    client.patch(f"/items/{item['id']}", json={"schedule": ["night"]})
    today = client.get(f"/patients/{pid}/today").json()
    assert today["slots"]["night"] == [] and today["waiting_approval"] == 1


def test_set_aside_items_leave_the_schedule(client):
    pid = household(client)
    expired = add(client, pid, "Tryptin", expiry="2020-01", schedule=["night"], pills_left=2, doses_per_day=1)
    current = add(client, pid, "Seclo", expiry="2099-01", schedule=["morning"])
    assert client.patch(f"/items/{current['id']}", json={"set_aside": True}).status_code == 422
    assert [x["brand"] for x in client.get(f"/patients/{pid}/cleanup").json()["to_set_aside"]] == ["Tryptin"]
    assert client.patch(f"/items/{expired['id']}", json={"set_aside": True}).status_code == 200
    client.post(f"/patients/{pid}/schedule/approve", json={"reviewer": "P"}, headers=TOKEN)
    today = client.get(f"/patients/{pid}/today").json()
    assert today["slots"]["night"] == [] and [m["brand"] for m in today["slots"]["morning"]] == ["Seclo"]
    passport = client.get(f"/patients/{pid}/passport").json()
    assert all(m["brand"] != "Tryptin" for g in passport["groups"].values() for m in g)
    assert client.get(f"/patients/{pid}/report").json()["refills_due"] == []
    assert client.get(f"/patients/{pid}/cleanup").json()["set_aside"][0]["brand"] == "Tryptin"


# ---- allergies, passport, emergency page -------------------------------------------------

def test_allergies_need_the_pharmacist_again_after_an_edit(client):
    pid = household(client)
    client.patch(f"/patients/{pid}", json={"allergies": ["Penicillin"]})
    client.post(f"/patients/{pid}/allergies/confirm", json={"reviewer": "Pharm"}, headers=TOKEN)
    assert client.get(f"/patients/{pid}/passport").json()["allergies_confirmed_by"] == "Pharm"
    client.patch(f"/patients/{pid}", json={"allergies": ["Penicillin", "Sulfa"]})
    assert client.get(f"/patients/{pid}/passport").json()["allergies_confirmed_by"] is None


def test_emergency_page_is_read_only_and_revocable(client):
    pid = household(client, name_bn="রহিমা বেগম")
    add(client, pid, "Seclo", schedule=["morning"])
    client.patch(f"/patients/{pid}", json={"allergies": ["Penicillin"], "emergency_contact_name": "Nusrat",
                                           "emergency_contact_phone": "+880 1000 000000"})
    assert client.get(f"/patients/{pid}/passport").json()["emergency_enabled"] is False
    token = client.post(f"/patients/{pid}/emergency").json()["token"]
    key = client.headers.pop("X-Family-Key")
    page = client.get(f"/emergency/{token}").json()  # no key, no login
    assert page["first_name"] == "রহিমা" and "বেগম" not in json.dumps(page, ensure_ascii=False)
    assert page["medicines"][0]["brand"] == "Seclo" and page["allergies"] == ["Penicillin"]
    assert page["emergency_contact"]["phone"] == "+880 1000 000000"
    assert client.get("/emergency/not-a-real-token-xx").status_code == 404
    client.delete(f"/patients/{pid}/emergency", headers={"X-Family-Key": key})
    assert client.get(f"/emergency/{token}").status_code == 404


def test_passport_lists_prescribers_and_last_review(client):
    pid = household(client)
    add(client, pid, "Napa", prescriber="Local drug shop", schedule=["morning"])
    add(client, pid, "Ace", prescriber="Village doctor", schedule=["night"])
    client.post(f"/patients/{pid}/check")
    fid = client.get(f"/patients/{pid}/flags?view=reviewer", headers=TOKEN).json()[0]["id"]
    client.post(f"/flags/{fid}/review", headers=TOKEN, json={"status": "confirmed", "reviewer": "Dr. R", "note": "ok"})
    p = client.get(f"/patients/{pid}/passport").json()
    assert {x["name"] for x in p["prescribers"]} == {"Local drug shop", "Village doctor"}
    assert p["last_reviewed"]["by"] == "Dr. R" and p["last_reviewed"]["role"] == "doctor"


# ---- FHIR --------------------------------------------------------------------------------

def test_fhir_bundle_shape(client):
    pid = household(client)
    add(client, pid, "Napa", strength="500 mg", schedule=["morning", "night"], prescriber="Local drug shop")
    b = client.get(f"/patients/{pid}/fhir").json()
    assert b["resourceType"] == "Bundle" and b["type"] == "collection"
    kinds = [e["resource"]["resourceType"] for e in b["entry"]]
    assert kinds == ["Patient", "MedicationStatement"]
    patient = b["entry"][0]["resource"]
    assert set(patient) == {"resourceType", "id", "active"}  # no name, no identifiers
    ms = b["entry"][1]["resource"]
    assert ms["status"] == "active" and ms["subject"]["reference"] == f"Patient/{patient['id']}"
    assert ms["medicationCodeableConcept"]["text"] == "Napa 500 mg (paracetamol)"
    assert ms["dosage"][0]["timing"]["repeat"]["when"] == ["MORN", "NIGHT"]
    assert all(e["fullUrl"] for e in b["entry"])


# ---- doctor visit ------------------------------------------------------------------------

def test_visit_prep_shows_changes_since_the_last_visit(client):
    pid = household(client)
    add(client, pid, "Napa")
    client.patch(f"/patients/{pid}", json={"visit_questions": ["Can the pressure tablets be reduced?"]})
    v = client.get(f"/patients/{pid}/visit").json()
    assert v["questions"] == ["Can the pressure tablets be reduced?"] and v["changes"] == []
    time.sleep(1.1)  # timestamps have one-second resolution
    assert client.post(f"/patients/{pid}/visit/done").json()["next"] == f"/p/{pid}/scan"
    time.sleep(1.1)
    ace = add(client, pid, "Ace")
    client.patch(f"/items/{ace['id']}/clinical", json={"stopped": True, "reviewer": "Pharm"}, headers=TOKEN)
    add(client, pid, "Seclo")
    v = client.get(f"/patients/{pid}/visit").json()
    assert v["questions"] == []
    assert {(c["kind"], c["brand"]) for c in v["changes"]} == {("added", "Seclo"), ("stopped", "Ace")}
