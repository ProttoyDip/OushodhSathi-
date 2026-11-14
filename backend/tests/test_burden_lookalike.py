"""Anticholinergic burden and look-alike / sound-alike name rules."""
from datetime import date
from itertools import combinations

from app.brands import match_brand
from app.models import RuleItem
from app.rules import anticholinergic_burden, look_alike_names, run_rules
from app.tables import load_brands, load_rule_tables

TODAY = date(2026, 11, 14)


def item(i, brand, generic=None, drug_class=None):
    if generic is None:
        m = match_brand(brand)
        generic, drug_class = m.generic, m.drug_class
    return RuleItem(id=i, brand=brand, generic=generic, drug_class=drug_class)


# --- anticholinergic burden -------------------------------------------------

def test_tryptin_alone_reaches_the_threshold_at_68():
    [flag] = anticholinergic_burden([item(1, "Tryptin")], 68, load_rule_tables().acb)
    assert flag.code == "ANTICHOLINERGIC_BURDEN"
    assert flag.severity == "amber" and flag.routed_to == "pharmacist"
    assert flag.meta["score"] == 3 and flag.meta["scores"] == {"amitriptyline": 3}


def test_burden_adds_up_across_medicines():
    acb = load_rule_tables().acb
    items = [item(1, "Tenoloc", "atenolol", "beta-blocker"), item(2, "Lasix", "furosemide", "loop-diuretic"),
             item(3, "Nidipin", "nifedipine", "CCB-dihydropyridine")]
    [flag] = anticholinergic_burden(items, 70, acb)
    assert flag.meta["score"] == 3 and flag.item_ids == [1, 2, 3]
    assert not anticholinergic_burden(items[:2], 70, acb)  # total 2: below the threshold


def test_combination_product_counts_each_ingredient_once():
    acb = load_rule_tables().acb
    items = [item(1, "Amdocal Plus"), item(2, "Tenoloc", "atenolol", "beta-blocker")]
    assert not anticholinergic_burden(items, 70, acb)  # atenolol twice still scores 1


def test_no_burden_flag_under_65_or_without_age():
    acb = load_rule_tables().acb
    assert not anticholinergic_burden([item(1, "Tryptin")], 60, acb)
    assert not anticholinergic_burden([item(1, "Tryptin")], None, acb)


def test_burden_flag_key_is_stable_across_reruns():
    acb = load_rule_tables().acb
    a = anticholinergic_burden([item(1, "Tryptin")], 68, acb)[0].key
    b = anticholinergic_burden([item(7, "Tryptin")], 68, acb)[0].key
    assert a == b


# --- look-alike / sound-alike names -----------------------------------------

def test_classic_look_alike_pairs_are_flagged():
    pairs = [("Celebrex", "celecoxib", "Celexa", "citalopram"),
             ("Lamictal", "lamotrigine", "Lamisil", "terbinafine"),
             ("Hydralazine", "hydralazine", "Hydroxyzine", "hydroxyzine")]
    for a, ga, b, gb in pairs:
        [flag] = look_alike_names([item(1, a, ga, ""), item(2, b, gb, "")])
        assert flag.code == "LOOK_ALIKE_NAMES" and flag.severity == "amber" and flag.routed_to == "pharmacist"
        assert flag.meta["looks_alike"], (a, b)


def test_sound_alike_pair_is_flagged():
    [flag] = look_alike_names([item(1, "Seclo"), item(2, "Ceclo", "cefaclor", "cephalosporin")])
    assert flag.meta["sound_alike"]


def test_same_medicine_is_not_a_look_alike():
    # Napa and Napa Extra share paracetamol: DUPLICATE_GENERIC covers it, not this rule
    assert not look_alike_names([item(1, "Napa"), item(2, "Napa Extra")])


def test_unknown_generic_is_never_compared():
    assert not look_alike_names([item(1, "Celebrex", "celecoxib", ""), item(2, "Celexa", None, None)])


def test_no_false_alarms_among_the_seed_brands():
    brands = sorted({row.brand for row in load_brands().values()})
    items = [item(i, b) for i, b in enumerate(brands, 1)]
    assert not look_alike_names(items)


def test_unrelated_names_are_not_flagged():
    for a, b in combinations(["Napa", "Comet", "Rivotril", "Angilock"], 2):
        assert not look_alike_names([item(1, a), item(2, b)])


# --- integration with the full engine ---------------------------------------

def test_demo_household_gets_a_burden_flag_and_no_look_alike():
    names = ["Napa", "Ace", "Camlodin", "Amdocal", "Angilock", "Clofenac", "Rivotril", "Tryptin", "Comet"]
    flags = run_rules([item(i, n) for i, n in enumerate(names, 1)], 68, load_rule_tables(), TODAY)
    codes = [f.code for f in flags]
    assert codes.count("ANTICHOLINERGIC_BURDEN") == 1
    assert "LOOK_ALIKE_NAMES" not in codes
    assert len({f.key for f in flags}) == len(flags)


# --- family-facing text -----------------------------------------------------

def test_new_codes_have_safe_bangla_templates():
    from datetime import datetime

    from app.explain import SAFETY_SENTENCE, is_good_bangla, is_safe, template
    from app.models import MedicineItem, StoredFlag

    now = datetime(2026, 11, 14)
    meds = [MedicineItem(id=1, patient_id=1, brand="Tryptin", generic="amitriptyline", created_at=now),
            MedicineItem(id=2, patient_id=1, brand="Seclo", generic="omeprazole", created_at=now)]
    for code in ("ANTICHOLINERGIC_BURDEN", "LOOK_ALIKE_NAMES"):
        flag = StoredFlag(id=1, patient_id=1, key="k", code=code, severity="amber", item_ids=[1, 2],
                          evidence="e", routed_to="pharmacist", data_source="d", status="confirmed",
                          created_at=now, updated_at=now)
        text = template(flag, meds)
        assert is_safe(text) and is_good_bangla(text), code
        assert text.endswith(SAFETY_SENTENCE)
        assert "একটি বিষয় দেখেছেন" not in text  # not the generic fallback
