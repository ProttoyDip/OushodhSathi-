"""Kidney function: CKD-EPI 2021 eGFR, KIDNEY_DOSE and KIDNEY_TEST_DUE."""
from datetime import date, datetime, timedelta

import pytest

from app.brands import match_brand
from app.kidney import KidneyContext, context_from, egfr_ckd_epi_2021, kdigo_stage, to_mg_dl
from app.models import MedicineItem, RuleItem, StoredFlag
from app.rules import kidney_dose, kidney_test_due, run_rules
from app.tables import load_rule_tables

TODAY = date(2026, 11, 14)
TOKEN = {"X-Reviewer-Token": "test-token"}


def item(i, brand):
    m = match_brand(brand)
    return RuleItem(id=i, brand=brand, generic=m.generic, drug_class=m.drug_class)


def renal():
    return load_rule_tables().renal


# --- the formula, against values worked from the published equation --------------------

@pytest.mark.parametrize("scr, age, sex, expected", [
    # male 50, Scr 1.0: 142 x 1 x (1.0/0.9)^-1.2 x 0.9938^50 = 142 x 0.8812 x 0.7328 = 91.7
    (1.0, 50, "male", 91.69),
    # female 68, Scr 1.4: 142 x (2.0)^-1.2 x 0.9938^68 x 1.012 = 142 x 0.4353 x 0.6551 x 1.012 = 41.0
    (1.4, 68, "female", 40.98),
    # female 40, Scr 0.6 (below kappa: the alpha branch): 142 x (0.857)^-0.241 x 0.9938^40 x 1.012 = 116.3
    (0.6, 40, "female", 116.30),
    # male 70, Scr 2.5
    (2.5, 70, "male", 26.96),
])
def test_ckd_epi_2021_worked_values(scr, age, sex, expected):
    assert egfr_ckd_epi_2021(scr, age, sex) == pytest.approx(expected, abs=0.05)


def test_umol_conversion():
    assert to_mg_dl(88.4, "umol/L") == pytest.approx(1.0)
    assert to_mg_dl(123.76, "umol/L") == pytest.approx(1.4)
    assert to_mg_dl(1.4, "mg/dL") == 1.4


def test_female_factor_and_kappa():
    """Same creatinine and age: the female equation uses kappa 0.7, alpha -0.241 and x1.012."""
    f = egfr_ckd_epi_2021(0.9, 60, "female")
    expected = 142 * (0.9 / 0.7) ** -1.200 * 0.9938 ** 60 * 1.012
    assert f == pytest.approx(expected)
    assert egfr_ckd_epi_2021(0.9, 60, "male") == pytest.approx(142 * 0.9938 ** 60)


def test_kdigo_stages():
    assert [kdigo_stage(v) for v in (95, 60, 59.9, 45, 44.9, 30, 29.9, 15, 14.9)] == \
        ["G1", "G2", "G3a", "G3a", "G3b", "G3b", "G4", "G4", "G5"]


def test_no_egfr_without_sex():
    ctx = context_from({"taken_on": "2026-10-01", "creatinine_mg_dl": 1.4}, 68, None)
    assert ctx.egfr is None and ctx.taken_on == date(2026, 10, 1)


# --- KIDNEY_DOSE ---------------------------------------------------------------------------

def test_lowest_band_wins():
    [flag] = kidney_dose([item(1, "Comet")], KidneyContext(egfr=25, taken_on=TODAY), renal())
    assert flag.severity == "red" and flag.routed_to == "doctor" and flag.meta["threshold"] == 30
    assert "fda" in flag.data_source.lower()


def test_amber_band_between_30_and_45():
    [flag] = kidney_dose([item(1, "Comet")], KidneyContext(egfr=41, taken_on=TODAY), renal())
    assert flag.severity == "amber" and flag.routed_to == "pharmacist" and flag.meta["threshold"] == 45
    assert "41" in flag.evidence and "2026-11-14" in flag.evidence


def test_no_flag_above_45_or_without_a_test():
    assert kidney_dose([item(1, "Comet")], KidneyContext(egfr=50, taken_on=TODAY), renal()) == []
    assert kidney_dose([item(1, "Comet")], KidneyContext(egfr=None, taken_on=None), renal()) == []
    assert kidney_dose([item(1, "Comet")], None, renal()) == []


def test_two_metformin_strips_share_one_flag():
    flags = kidney_dose([item(1, "Comet"), item(2, "Comet")], KidneyContext(egfr=41, taken_on=TODAY), renal())
    assert len(flags) == 1 and flags[0].item_ids == [1, 2]


# --- KIDNEY_TEST_DUE -----------------------------------------------------------------------

def test_test_due_after_a_year_not_before():
    meds = [item(1, "Comet")]
    assert kidney_test_due(meds, KidneyContext(egfr=60, taken_on=TODAY - timedelta(days=366)), TODAY)
    assert not kidney_test_due(meds, KidneyContext(egfr=60, taken_on=TODAY - timedelta(days=364)), TODAY)


def test_test_due_when_never_tested_only_with_metformin():
    [flag] = kidney_test_due([item(1, "Comet")], KidneyContext(egfr=None, taken_on=None), TODAY)
    assert flag.severity == "amber" and flag.routed_to == "pharmacist"
    assert not kidney_test_due([item(1, "Napa")], KidneyContext(egfr=None, taken_on=None), TODAY)


def test_unknown_context_skips_kidney_rules():
    codes = {f.code for f in run_rules([item(1, "Comet")], 68, load_rule_tables(), TODAY)}
    assert not codes & {"KIDNEY_DOSE", "KIDNEY_TEST_DUE"}


# --- through the API ----------------------------------------------------------------------

def household(client):
    r = client.post("/patients", json={"name": "Kidney Home", "age": 68, "consent": True})
    pid, h = r.json()["id"], {"X-Family-Key": r.json()["family_key"]}
    client.post(f"/patients/{pid}/items?confirmed=true", json={"brand": "Comet"}, headers=h)
    return pid, h


def test_family_never_sees_pending_kidney_flags(client):
    pid, h = household(client)
    client.patch(f"/patients/{pid}", json={"sex": "female"}, headers=h)
    client.post(f"/patients/{pid}/check", headers=h)
    r = client.post(f"/patients/{pid}/kidney-tests", headers=TOKEN,
                    json={"creatinine": 123.76, "unit": "umol/L", "taken_on": "2026-11-01"})
    assert r.status_code == 201, r.text
    assert r.json()["latest"]["creatinine_mg_dl"] == 1.4 and r.json()["latest"]["stage"] == "G3b"
    reviewer = client.get(f"/patients/{pid}/flags?view=reviewer", headers=TOKEN).json()
    codes = {f["code"] for f in reviewer}
    assert "KIDNEY_DOSE" in codes and "KIDNEY_TEST_DUE" not in codes  # a recent test resolves "due"
    assert client.get(f"/patients/{pid}/flags?view=family", headers=h).json() == []


def test_kidney_endpoints_are_reviewer_only_and_validated(client):
    pid, h = household(client)
    body = {"creatinine": 1.2, "unit": "mg/dL", "taken_on": "2026-11-01"}
    assert client.post(f"/patients/{pid}/kidney-tests", headers=h, json=body).status_code == 401
    assert client.get(f"/patients/{pid}/kidney", headers=h).status_code == 401
    for bad in ({"creatinine": 25, "unit": "mg/dL"}, {"creatinine": 0.1, "unit": "mg/dL"},
                {"creatinine": 1.0, "unit": "mg/dL", "taken_on": "2999-01-01"}):
        assert client.post(f"/patients/{pid}/kidney-tests", headers=TOKEN,
                           json={"taken_on": "2026-11-01", **bad}).status_code == 422
    view = client.get(f"/patients/{pid}/kidney", headers=TOKEN).json()
    assert view["latest"] is None and view["equation"].startswith("CKD-EPI 2021")


def test_export_and_delete_include_kidney_tests(client, store):
    pid, h = household(client)
    client.post(f"/patients/{pid}/kidney-tests", headers=TOKEN,
                json={"creatinine": 1.1, "unit": "mg/dL", "taken_on": "2026-10-20"})
    data = client.get(f"/patients/{pid}/export", headers=h).json()
    assert data["kidney_tests"][0]["creatinine_mg_dl"] == 1.1
    client.request("DELETE", f"/patients/{pid}", headers=h, json={"confirm": "DELETE"})
    assert store._all("SELECT * FROM kidney_tests WHERE patient_id = ?", (pid,)) == []


def test_demo_household_shows_one_amber_kidney_dose_on_comet(store):
    from app.demo_seed import seed_demo

    pid = seed_demo(store, "pending")["patient_id"]
    flags = [f for f in store.list_flags(pid) if f.code.startswith("KIDNEY")]
    assert [(f.code, f.severity) for f in flags] == [("KIDNEY_DOSE", "amber")]
    comet = [it.id for it in store.list_items(pid) if it.brand == "Comet"]
    assert flags[0].item_ids == comet


def test_kidney_templates_are_safe_bangla():
    from app.explain import SAFETY_SENTENCE, is_good_bangla, is_safe, template

    now = datetime(2026, 11, 14)
    meds = [MedicineItem(id=1, patient_id=1, brand="Comet", generic="metformin", created_at=now)]
    for code, meta in (("KIDNEY_DOSE", {"note_bn": renal()[1].note_bn}), ("KIDNEY_TEST_DUE", {})):
        flag = StoredFlag(id=1, patient_id=1, key="k", code=code, severity="amber", item_ids=[1], evidence="e",
                          routed_to="pharmacist", data_source="d", status="confirmed", created_at=now, meta=meta)
        text = template(flag, meds)
        assert is_safe(text) and is_good_bangla(text), (code, text)
        assert text.endswith(SAFETY_SENTENCE) and "কিডনি" in text
        assert "একটি বিষয় দেখেছেন" not in text
