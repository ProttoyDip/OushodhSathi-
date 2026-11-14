"""TRIPLE_WHAMMY: ACE inhibitor or ARB + diuretic + NSAID in the same house."""
from datetime import date, datetime

from app.brands import match_brand
from app.models import MedicineItem, RuleItem, StoredFlag
from app.rules import run_rules, triple_whammy
from app.tables import load_rule_tables

TODAY = date(2026, 11, 14)


def item(i, brand):
    m = match_brand(brand)
    assert m.generic, f"{brand} should be in the brand seed"
    return RuleItem(id=i, brand=brand, generic=m.generic, drug_class=m.drug_class)


def groups():
    return load_rule_tables().class_groups


def test_combination_product_covers_raas_and_diuretic():
    """Osartil Plus (losartan + hydrochlorothiazide) + Clofenac (diclofenac): all three groups."""
    [flag] = triple_whammy([item(1, "Osartil Plus"), item(2, "Clofenac")], groups())
    assert flag.code == "TRIPLE_WHAMMY"
    assert flag.severity == "red" and flag.routed_to == "doctor"
    assert flag.item_ids == [1, 2]
    assert flag.meta == {"raas": ["losartan"], "diuretic": ["hydrochlorothiazide"], "nsaid": ["diclofenac"]}
    assert "medsafe" in flag.data_source.lower()


def test_no_diuretic_no_flag():
    assert triple_whammy([item(1, "Angilock"), item(2, "Clofenac")], groups()) == []


def test_ace_inhibitor_loop_diuretic_and_nsaid():
    [flag] = triple_whammy([item(1, "Ramace"), item(2, "Lasix"), item(3, "Naprosyn")], groups())
    assert flag.meta == {"raas": ["ramipril"], "diuretic": ["furosemide"], "nsaid": ["naproxen"]}
    assert flag.item_ids == [1, 2, 3]


def test_same_household_twice_gives_the_same_key():
    meds = [item(1, "Ramace"), item(2, "Lasix"), item(3, "Naprosyn")]
    assert triple_whammy(meds, groups())[0].key == triple_whammy(list(reversed(meds)), groups())[0].key


def test_one_flag_even_with_several_members_per_group():
    meds = [item(1, "Ramace"), item(2, "Osartil Plus"), item(3, "Lasix"), item(4, "Naprosyn"), item(5, "Clofenac")]
    flags = triple_whammy(meds, groups())
    assert len(flags) == 1 and flags[0].item_ids == [1, 2, 3, 4, 5]


def test_missing_table_never_fires():
    assert triple_whammy([item(1, "Osartil Plus"), item(2, "Clofenac")], {}) == []


def test_full_demo_household_has_no_triple_whammy():
    """Rahima's shelf has an ARB (Angilock) and an NSAID (Clofenac) but no diuretic."""
    names = ["Napa", "Ace", "Camlodin", "Amdocal", "Angilock", "Clofenac", "Rivotril", "Tryptin", "Comet"]
    flags = run_rules([item(i, n) for i, n in enumerate(names, 1)], 68, load_rule_tables(), TODAY)
    codes = [f.code for f in flags]
    assert "TRIPLE_WHAMMY" not in codes
    assert "INTERACTION" in codes  # the pairwise NSAID + ARB finding is kept


def test_engine_keeps_the_pairwise_interaction_alongside_the_triple():
    flags = run_rules([item(1, "Osartil Plus"), item(2, "Clofenac")], 70, load_rule_tables(), TODAY)
    codes = [f.code for f in flags]
    assert codes.count("TRIPLE_WHAMMY") == 1
    assert len({f.key for f in flags}) == len(flags)


def test_template_is_safe_bangla():
    from app.explain import SAFETY_SENTENCE, is_good_bangla, is_safe, template

    now = datetime(2026, 11, 14)
    meds = [MedicineItem(id=1, patient_id=1, brand="Osartil Plus", generic="losartan + hydrochlorothiazide", created_at=now),
            MedicineItem(id=2, patient_id=1, brand="Clofenac", generic="diclofenac", created_at=now)]
    flag = StoredFlag(id=1, patient_id=1, key="k", code="TRIPLE_WHAMMY", severity="red", item_ids=[1, 2],
                      evidence="e", routed_to="doctor", data_source="d", status="confirmed", created_at=now)
    text = template(flag, meds)
    assert is_safe(text) and is_good_bangla(text)
    assert text.endswith(SAFETY_SENTENCE)
    assert "কিডনি" in text and "ডাক্তার" in text
    assert "একটি বিষয় দেখেছেন" not in text


def test_email_labels_exist():
    from app import notify

    assert "TRIPLE_WHAMMY" in notify.CODE_BN and "TRIPLE_WHAMMY" in notify.CODE_EN
