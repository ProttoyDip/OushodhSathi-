"""STOPP/START v3 engine: verified rows only; START is never a family finding.

The rows below are FAKE test fixtures, not real criteria: real ones are entered and verified by
our pharmacist from O'Mahony et al., Eur Geriatr Med 2023.
"""
from datetime import date, datetime

from app.brands import match_brand
from app.models import MedicineItem, RuleItem, StoredFlag
from app.rules import run_rules, start_omissions, stopp_criteria
from app.tables import load_rule_tables, load_stopp_start

TODAY = date(2026, 11, 14)
FAKE = """# test fixture
id,kind,condition,drug_target,absent_target,text_en,source,verified
TEST-STOPP-1,STOPP,,class:nsaid,class:ppi,"Test: NSAID without a stomach protector.",fixture,yes
TEST-START-1,START,type 2 diabetes,,class:statin,"Test: possible statin omission.",fixture,yes
TEST-STOPP-2,STOPP,,class:benzodiazepine,,"Unverified row: must never fire.",fixture,no
"""


def rows(tmp_path):
    p = tmp_path / "stopp_start.csv"
    p.write_text(FAKE, encoding="utf-8")
    return load_stopp_start(p)


def item(i, brand):
    m = match_brand(brand)
    return RuleItem(id=i, brand=brand, generic=m.generic, drug_class=m.drug_class)


def test_only_verified_rows_are_loaded(tmp_path):
    assert [r.id for r in rows(tmp_path)] == ["TEST-STOPP-1", "TEST-START-1"]


def test_stopp_row_fires_when_target_present_and_absent_target_missing(tmp_path):
    [flag] = stopp_criteria([item(1, "Clofenac")], [], rows(tmp_path))
    assert flag.code == "STOPP_CRITERION" and flag.severity == "amber" and flag.routed_to == "pharmacist"
    assert flag.meta["criterion"] == "TEST-STOPP-1" and "STOPP/START v3" in flag.data_source
    # a stomach protector in the house: the criterion does not apply
    assert stopp_criteria([item(1, "Clofenac"), item(2, "Seclo")], [], rows(tmp_path)) == []
    # unknown conditions (None) skip the engine entirely
    assert stopp_criteria([item(1, "Clofenac")], None, rows(tmp_path)) == []


def test_unverified_rows_never_fire(tmp_path):
    assert all(f.meta["criterion"] != "TEST-STOPP-2" for f in stopp_criteria([item(1, "Rivotril")], [], rows(tmp_path)))


def test_start_rows_are_reviewer_notes_never_flags(tmp_path):
    notes = start_omissions([item(1, "Comet")], ["type 2 diabetes"], rows(tmp_path))
    assert [n["criterion"] for n in notes] == ["TEST-START-1"]
    assert start_omissions([item(1, "Comet"), item(2, "Atova")], ["type 2 diabetes"], rows(tmp_path)) == []
    assert start_omissions([item(1, "Comet")], ["hypertension"], rows(tmp_path)) == []  # condition not present
    # the engine never turns a START row into a flag
    from app.tables import RuleTables
    tables = RuleTables(stopp_start=rows(tmp_path))
    flags = run_rules([item(1, "Comet")], 70, tables, TODAY, conditions=["type 2 diabetes"])
    assert all(f.code != "STOPP_CRITERION" or f.meta["criterion"].startswith("TEST-STOPP") for f in flags)
    assert not any("START" in f.meta.get("criterion", "") for f in flags)


def test_shipped_table_is_empty_so_nothing_fires():
    assert load_rule_tables().stopp_start == ()
    names = ["Napa", "Ace", "Camlodin", "Amdocal", "Angilock", "Clofenac", "Rivotril", "Tryptin", "Comet"]
    flags = run_rules([item(i, n) for i, n in enumerate(names, 1)], 68, load_rule_tables(), TODAY,
                      conditions=["hypertension", "type 2 diabetes"])
    assert "STOPP_CRITERION" not in {f.code for f in flags}


def test_start_notes_endpoint_is_reviewer_only(client):
    r = client.post("/patients", json={"name": "S", "age": 70, "consent": True, "conditions": ["type 2 diabetes"]})
    pid, h = r.json()["id"], {"X-Family-Key": r.json()["family_key"]}
    assert client.get(f"/patients/{pid}/start-notes", headers=h).status_code == 401
    assert client.get(f"/patients/{pid}/start-notes", headers={"X-Reviewer-Token": "test-token"}).json() == []


def test_stopp_template_is_safe():
    from app.explain import SAFETY_SENTENCE, is_good_bangla, is_safe, template

    now = datetime(2026, 11, 14)
    meds = [MedicineItem(id=1, patient_id=1, brand="Clofenac", generic="diclofenac", created_at=now)]
    flag = StoredFlag(id=1, patient_id=1, key="k", code="STOPP_CRITERION", severity="amber", item_ids=[1],
                      evidence="e", routed_to="pharmacist", data_source="d", status="confirmed", created_at=now)
    text = template(flag, meds)
    assert is_safe(text) and is_good_bangla(text) and text.endswith(SAFETY_SENTENCE)
    assert "শুরু" not in text.replace(SAFETY_SENTENCE, "")  # never "start"
