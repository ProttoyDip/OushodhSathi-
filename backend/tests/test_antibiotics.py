"""Antibiotics: WHO AWaRe groups and ANTIBIOTIC_NO_PRESCRIPTION."""
from datetime import datetime

from app.brands import match_brand
from app.models import MedicineItem, RuleItem, StoredFlag
from app.rules import antibiotic_no_prescription
from app.tables import aware_group, load_aware


def item(i, brand, kind="unknown"):
    m = match_brand(brand)
    return RuleItem(id=i, brand=brand, generic=m.generic, drug_class=m.drug_class, prescriber_kind=kind)


def test_watch_from_a_drug_shop_is_amber_for_the_pharmacist():
    [flag] = antibiotic_no_prescription([item(1, "Zimax", "drug_shop")])
    assert flag.code == "ANTIBIOTIC_NO_PRESCRIPTION"
    assert flag.severity == "amber" and flag.routed_to == "pharmacist"
    assert flag.meta["aware_group"] == "Watch" and "drug shop" in flag.evidence


def test_watch_with_a_doctor_is_fine():
    assert antibiotic_no_prescription([item(1, "Zimax", "doctor")]) == []


def test_watch_self_and_unknown_are_flagged():
    assert antibiotic_no_prescription([item(1, "Ciprocin", "self")])
    assert antibiotic_no_prescription([item(1, "Cef-3")])  # default prescriber_kind is unknown


def test_reserve_is_red_for_the_doctor_always():
    [flag] = antibiotic_no_prescription([item(1, "Linez", "doctor")])
    assert flag.severity == "red" and flag.routed_to == "doctor" and flag.meta["aware_group"] == "Reserve"


def test_access_is_never_flagged():
    assert antibiotic_no_prescription([item(1, "Moxacil", "self"), item(2, "Filmet", "drug_shop")]) == []


def test_unknown_generic_and_non_antibiotics_are_ignored():
    unknown = RuleItem(id=1, brand="Mysterycillin", generic=None, prescriber_kind="drug_shop")
    assert antibiotic_no_prescription([unknown, item(2, "Napa", "drug_shop")]) == []


def test_aware_lookup_handles_combinations():
    assert aware_group("Amoxicillin + Clavulanic acid") == "Access"
    assert aware_group("azithromycin") == "Watch"
    assert aware_group("paracetamol") is None and aware_group(None) is None
    # every seed row is one of the three groups
    assert set(load_aware().values()) <= {"Access", "Watch", "Reserve"}


def test_medicine_items_carry_their_aware_group():
    now = datetime(2026, 11, 14)
    assert MedicineItem(id=1, patient_id=1, brand="Zimax", generic="azithromycin", created_at=now).aware_group == "Watch"
    assert MedicineItem(id=1, patient_id=1, brand="Napa", generic="paracetamol", created_at=now).aware_group is None


def test_prescriber_kind_round_trips_through_the_api(client):
    r = client.post("/patients", json={"name": "Abx Home", "age": 60, "consent": True})
    pid, h = r.json()["id"], {"X-Family-Key": r.json()["family_key"]}
    it = client.post(f"/patients/{pid}/items?confirmed=true", json={"brand": "Zimax"}, headers=h).json()
    assert it["prescriber_kind"] == "unknown" and it["aware_group"] == "Watch"
    client.post(f"/patients/{pid}/check", headers=h)
    reviewer = client.get(f"/patients/{pid}/flags?view=reviewer", headers={"X-Reviewer-Token": "test-token"}).json()
    assert [f["code"] for f in reviewer] == ["ANTIBIOTIC_NO_PRESCRIPTION"]
    assert client.patch(f"/items/{it['id']}", json={"prescriber_kind": "doctor"}, headers=h).json()["prescriber_kind"] == "doctor"
    client.post(f"/patients/{pid}/check", headers=h)
    reviewer = client.get(f"/patients/{pid}/flags?view=reviewer", headers={"X-Reviewer-Token": "test-token"}).json()
    assert reviewer == []  # resolved: the doctor prescribed it
    assert client.patch(f"/items/{it['id']}", json={"prescriber_kind": "pharmacy"}, headers=h).status_code == 422


def test_templates_are_safe_and_never_instruct():
    from app.explain import SAFETY_SENTENCE, is_good_bangla, is_safe, template

    now = datetime(2026, 11, 14)
    meds = [MedicineItem(id=1, patient_id=1, brand="Zimax", generic="azithromycin", created_at=now)]
    for group, severity, routed in (("Watch", "amber", "pharmacist"), ("Reserve", "red", "doctor")):
        flag = StoredFlag(id=1, patient_id=1, key="k", code="ANTIBIOTIC_NO_PRESCRIPTION", severity=severity,
                          item_ids=[1], evidence="e", routed_to=routed, data_source="d", status="confirmed",
                          created_at=now, meta={"aware_group": group})
        text = template(flag, meds)
        assert is_safe(text) and is_good_bangla(text), text
        assert text.endswith(SAFETY_SENTENCE) and "এন্টিবায়োটিক" in text
        # never "stop" and never "finish the course"
        body = text.replace(SAFETY_SENTENCE, "")
        assert "বন্ধ" not in body and "কোর্স শেষ" not in body and "শেষ করুন" not in body
