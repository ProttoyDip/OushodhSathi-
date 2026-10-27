"""Prompt 11: lower-price same generic, Ramadan plan, family activity, demo reset, photo rule."""
import asyncio
import json
import time

import pytest

from app import agent, guard, sathi
from app.models import MedicineItem
from app.savings import NOTICE_BN, find_savings

TOKEN = {"X-Reviewer-Token": "test-token"}
APPROVED = "2026-10-01T00:00:00+00:00"


def med(**kw) -> MedicineItem:
    base = dict(id=1, patient_id=1, brand="Angilock", generic="losartan", strength="50 mg", form="tablet",
                confirmed=True, doses_per_day=1, schedule=["morning"], schedule_approved_at=APPROVED)
    return MedicineItem(**{**base, **kw})


# ---- same generic, lower price -------------------------------------------------------------

def test_cheaper_brand_of_the_exact_same_product():
    out = find_savings([med()], set())
    [row] = out["items"]
    assert row["alternative"]["brand"] == "Osartil" and row["current_mrp_bdt"] == 10.0
    assert row["monthly_bdt"] == 60 and row["yearly_bdt"] == 730  # 2 taka a tablet, once a day
    assert out["total_yearly_bdt"] == 730 and out["notice_bn"] == NOTICE_BN
    assert "verify MRP" in out["price_note"]


def test_tablets_per_day_multiply_the_saving():
    [row] = find_savings([med(doses_per_day=2, per_dose=2)], set())["items"]
    assert row["tablets_per_day"] == 4 and row["yearly_bdt"] == 2920


@pytest.mark.parametrize("change", [
    {"strength": "100 mg"},          # another strength: Osartil's reference pack is 50 mg
    {"form": "syrup"},               # another form
    {"brand": "Osartil Plus", "generic": "losartan + hydrochlorothiazide", "strength": "50 mg + 12.5 mg"},  # FDC: no cheaper twin
])
def test_only_identical_generic_strength_and_form_match(change):
    assert find_savings([med(**change)], set())["items"] == []


def test_a_combination_never_matches_its_single_ingredient_cousin():
    # Amdocal Plus (amlodipine + atenolol) is not "amlodipine", however much cheaper Amdocal is
    out = find_savings([med(brand="Amdocal Plus", generic="amlodipine + atenolol", strength="5 mg + 25 mg")], set())
    assert out["items"] == []


@pytest.mark.parametrize("change", [
    {"stopped": True}, {"set_aside": True}, {"confirmed": False},
    {"schedule_approved_at": None}, {"doses_per_day": None},
])
def test_stopped_set_aside_unconfirmed_or_unapproved_are_excluded(change):
    assert find_savings([med(**change)], set())["items"] == []


def test_items_in_a_duplicate_finding_wait_for_the_reviewer():
    assert find_savings([med(id=7)], {7})["items"] == []


def test_savings_endpoint_excludes_duplicates(client):
    pid = client.post("/patients", json={"name": "Savings", "age": 70}).json()
    client.headers["X-Family-Key"] = pid["family_key"]
    pid = pid["id"]
    for brand, strength in (("Angilock", "50 mg"), ("Camlodin", "5 mg"), ("Amdocal", "5 mg")):
        client.post(f"/patients/{pid}/items?confirmed=true",
                    json={"brand": brand, "strength": strength, "form": "tablet", "schedule": ["morning"], "doses_per_day": 1})
    client.post(f"/patients/{pid}/check")
    client.post(f"/patients/{pid}/schedule/approve", json={"reviewer": "P"}, headers=TOKEN)
    rows = client.get(f"/patients/{pid}/savings").json()["items"]
    # Camlodin and Amdocal are a duplicate pair (amlodipine): no price suggestion for them
    assert [r["brand"] for r in rows] == ["Angilock"]


# ---- Ramadan ---------------------------------------------------------------------------------

def household(client):
    r = client.post("/patients", json={"name": "Ramadan", "age": 66}).json()
    client.headers["X-Family-Key"] = r["family_key"]
    pid = r["id"]
    ids = [client.post(f"/patients/{pid}/items?confirmed=true",
                       json={"brand": b, "schedule": s, "doses_per_day": len(s)}).json()["id"]
           for b, s in (("Comet", ["morning", "night"]), ("Angilock", ["morning"]), ("Atova", ["night"]))]
    client.post(f"/patients/{pid}/schedule/approve", json={"reviewer": "P"}, headers=TOKEN)
    return pid, ids


def test_a_request_never_changes_todays_medicines(client):
    pid, _ = household(client)
    before = client.get(f"/patients/{pid}/today").json()
    assert client.post(f"/patients/{pid}/ramadan-request").json()["ramadan_status"] == "requested"
    after = client.get(f"/patients/{pid}/today").json()
    assert after["slots"] == before["slots"] and after["ramadan"] is None and after["ramadan_status"] == "requested"
    assert [r["patient"]["id"] for r in client.get("/ramadan/requests", headers=TOKEN).json()] == [pid]
    assert client.get("/ramadan/requests").status_code == 401


def test_only_a_reviewer_approves_a_ramadan_plan(client):
    pid, (comet, angilock, atova) = household(client)
    client.post(f"/patients/{pid}/ramadan-request")
    plan = {"reviewer": "Dr. R", "note": "Metformin split between sehri and iftar; check sugar if unwell.",
            "items": [{"item_id": comet, "slots": ["iftar", "sehri"]}, {"item_id": angilock, "slots": ["iftar"]}]}
    assert client.post(f"/patients/{pid}/ramadan-approve", json=plan).status_code == 401
    r = client.post(f"/patients/{pid}/ramadan-approve", json=plan, headers=TOKEN).json()
    ram = r["ramadan"]
    assert [m["brand"] for m in ram["sehri"]] == ["Comet"]
    assert sorted(m["brand"] for m in ram["iftar"]) == ["Angilock", "Comet"]
    assert [m["brand"] for m in ram["not_in_plan"]] == ["Atova"]  # nothing disappears silently
    assert ram["approved_by"] == "Dr. R" and r["ramadan_status"] == "approved"
    assert client.get("/ramadan/requests", headers=TOKEN).json() == []
    # the family ends it after Ramadan: back to the usual times
    client.delete(f"/patients/{pid}/ramadan")
    t = client.get(f"/patients/{pid}/today").json()
    assert t["ramadan"] is None and [m["brand"] for m in t["slots"]["morning"]] == ["Comet", "Angilock"]


def test_ramadan_plan_rejects_other_households_items(client):
    pid, _ = household(client)
    other = client.post("/patients", json={"name": "Other", "age": 70}).json()
    item = client.post(f"/patients/{other['id']}/items?confirmed=true", json={"brand": "Napa"},
                       headers={"X-Family-Key": other["family_key"]}).json()
    r = client.post(f"/patients/{pid}/ramadan-approve", headers=TOKEN,
                    json={"reviewer": "P", "note": "ok ok", "items": [{"item_id": item["id"], "slots": ["sehri"]}]})
    assert r.status_code == 422


@pytest.mark.parametrize("q", ["রোজা রেখে ওষুধ খাব কীভাবে?", "Ramzan e sehri te insulin kokhon nibo?",
                               "Can Ma take her metformin at iftar during Ramadan?", "ইফতারে কোন ওষুধ?"])
def test_fasting_questions_go_to_the_pharmacist(q):
    assert guard.looks_medical(q)
    assert sathi.ask(q, "bn", 1, None).kind == "medical_redirect"


# ---- family activity -------------------------------------------------------------------------

def test_activity_records_milestones_without_names(client):
    pid, _ = household(client)
    client.post(f"/patients/{pid}/check")
    client.post(f"/patients/{pid}/bp", json={"systolic": 150, "diastolic": 95})
    client.post(f"/patients/{pid}/ramadan-request")
    log = client.get(f"/patients/{pid}/activity").json()
    kinds = [a["kind"] for a in log]
    assert kinds[:4] == ["ramadan_requested", "bp_logged", "sent_for_review", "schedule_approved"]
    assert next(a for a in log if a["kind"] == "sent_for_review")["n"] == 3
    assert all(set(a) == {"kind", "n", "created_at"} for a in log)
    assert "Comet" not in json.dumps(log) and "Ramadan" not in json.dumps(log)


# ---- demo reset ------------------------------------------------------------------------------

def _demo(client, store):
    from app.demo_seed import seed_demo

    seed_demo(store, "pending")
    return next(p.id for p in store.list_patients() if p.is_demo)


def test_demo_reset_gives_both_views_something_to_show(client, store):
    pid = _demo(client, store)
    client.post(f"/patients/{pid}/questions", json={"text": "left over from a judge"})
    started = time.perf_counter()
    r = client.post("/demo/reset").json()
    assert time.perf_counter() - started < 1.0
    assert r["patient_id"] == pid and r["confirmed"] == 2 and r["pending"] >= 3
    family = client.get(f"/patients/{pid}/flags").json()
    assert sorted(sorted(i["brand"] for i in f["items"]) for f in family) == [["Ace", "Napa"], ["Angilock", "Clofenac"]]
    assert all(f["explanation_bn"] and f["note"] for f in family)
    queue = client.get("/flags", headers=TOKEN).json()
    pending = {(f["code"], tuple(sorted(i["brand"] for i in f["items"]))) for f in queue["flags"]}
    assert ("DUPLICATE_GENERIC", ("Amdocal", "Camlodin")) in pending
    assert ("INTERACTION", ("Rivotril", "Tryptin")) in pending and ("EXPIRED", ("Tryptin",)) in pending
    assert queue["counts"]["red"] >= 1 and queue["counts"]["amber"] >= 1
    assert client.get(f"/patients/{pid}/questions").json() == []  # the next judge starts clean


def test_demo_reset_never_touches_real_households(client, store):
    _demo(client, store)
    real = client.post("/patients", json={"name": "Real", "age": 70}).json()
    h = {"X-Family-Key": real["family_key"]}
    client.post(f"/patients/{real['id']}/items?confirmed=true", json={"brand": "Napa"}, headers=h)
    client.post("/demo/reset")
    assert [i["brand"] for i in client.get(f"/patients/{real['id']}/items", headers=h).json()] == ["Napa"]


# ---- photos: prescriptions never get a thumbnail -------------------------------------------

def test_prescription_photos_get_no_thumbnail(monkeypatch):
    extracted = {
        b"strip": [agent.ExtractedItem(brand="Napa", strength="500 mg", source="strip", confidence=0.9)],
        b"rx": [agent.ExtractedItem(brand="Seclo", strength="20 mg", source="prescription", confidence=0.9),
                agent.ExtractedItem(brand="Ace", strength="500 mg", source="strip", confidence=0.9)],
    }

    async def fake_extract(photo, providers, router, deps):
        return extracted[photo], "fake", "fake-model", False

    monkeypatch.setattr(agent, "configured_providers", lambda task, client=None: ["fake"])
    monkeypatch.setattr(agent, "_extract_one", fake_extract)
    out = asyncio.run(agent.read_shelf([b"strip", b"rx"], router=object()))
    thumbs = {s.item.brand: s.thumbnail for s in out.items}
    assert thumbs["Napa"] is not None
    # a photo with a prescription in it may show the patient's name: nothing from it is kept
    assert thumbs["Seclo"] is None and thumbs["Ace"] is None
