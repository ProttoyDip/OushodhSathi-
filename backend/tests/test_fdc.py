"""Fixed-dose combinations (FDC) and the chronic-care (hypertension + diabetes) rules."""
from datetime import date

from app.brands import match_brand
from app.models import RuleItem
from app.rules import run_rules
from app.tables import load_rule_tables

TODAY = date(2026, 10, 27)


def items(*brands: str, prescribers: tuple[str, ...] = ()) -> list[RuleItem]:
    out = []
    for i, b in enumerate(brands, start=1):
        m = match_brand(b)
        assert m.generic, f"{b} must be in the brand table"
        out.append(RuleItem(id=i, brand=b, generic=m.generic, drug_class=m.drug_class,
                            prescriber=prescribers[i - 1] if prescribers else f"prescriber {i}"))
    return out


def flags(*brands: str, age: int = 70):
    return run_rules(items(*brands), age, load_rule_tables(), TODAY)


def codes(fs) -> list[tuple[str, str]]:
    return sorted((f.code, f.severity) for f in fs)


def test_napa_extra_and_ace_are_both_paracetamol():
    fs = flags("Napa Extra", "Ace")
    dup = [f for f in fs if f.code == "DUPLICATE_GENERIC"]
    assert len(dup) == 1 and dup[0].meta["generic"] == "paracetamol" and dup[0].item_ids == [1, 2]
    assert dup[0].severity == "red" and dup[0].routed_to == "doctor"
    assert "caffeine" not in dup[0].evidence.split("contain")[1]  # the shared ingredient only


def test_combination_duplicate_is_not_also_a_class_duplicate():
    fs = flags("Amdocal Plus", "Camlodin")
    assert [f.meta["generic"] for f in fs if f.code == "DUPLICATE_GENERIC"] == ["amlodipine"]
    assert not [f for f in fs if f.code == "THERAPEUTIC_DUPLICATION"]


def test_losartan_twice_through_a_combination():
    fs = flags("Osartil Plus", "Angilock")
    assert [f.meta["generic"] for f in fs if f.code == "DUPLICATE_GENERIC"] == ["losartan"]


def test_beta_blocker_inside_a_combination_masks_low_sugar_with_a_sulfonylurea():
    fs = flags("Amdocal Plus", "Secrin")
    inter = [f for f in fs if f.code == "INTERACTION"]
    assert len(inter) == 1
    f = inter[0]
    assert f.severity == "red" and f.routed_to == "doctor" and f.meta["interaction_severity"] == "major"
    assert "(atenolol)" in f.evidence and "(glimepiride)" in f.evidence
    assert "mask warning signs" in f.evidence and f.meta["effect_bn"]


def test_steroid_with_metformin_goes_to_the_pharmacist():
    [f] = [f for f in flags("Oradexon", "Comet") if f.code == "INTERACTION"]
    assert (f.severity, f.routed_to) == ("amber", "pharmacist")
    assert "raise blood sugar" in f.evidence


def test_nsaid_with_metformin_goes_to_the_pharmacist():
    [f] = [f for f in flags("Clofenac", "Comet") if f.code == "INTERACTION"]
    assert (f.severity, f.routed_to) == ("amber", "pharmacist") and "kidney" in f.evidence


def test_nsaid_meets_the_arb_inside_a_combination():
    [f] = [f for f in flags("Osartil Plus", "Clofenac") if f.code == "INTERACTION"]
    assert "(losartan)" in f.evidence and "(diclofenac)" in f.evidence


def test_ingredients_of_one_product_never_interact_with_each_other():
    assert not [f for f in flags("Amdocal Plus") if f.code == "INTERACTION"]


def test_same_class_through_a_combination_is_a_therapeutic_duplicate():
    fdc = items("Amdocal Plus")[0]
    bisoprolol = RuleItem(id=2, brand="Bisocor", generic="bisoprolol", drug_class="beta-blocker", prescriber="x")
    fs = run_rules([fdc, bisoprolol], 60, load_rule_tables(), TODAY)
    [f] = [f for f in fs if f.code == "THERAPEUTIC_DUPLICATION"]
    assert f.meta["generics"] == ["atenolol", "bisoprolol"] and f.meta["drug_class"] == "beta-blocker"


def test_sulfonylurea_is_on_the_beers_list_from_65():
    assert [f.meta["target"] for f in flags("Secrin", age=70) if f.code == "BEERS_65"] == ["class:sulfonylurea"]
    assert not [f for f in flags("Secrin", age=60) if f.code == "BEERS_65"]


def test_beers_checks_each_ingredient_of_a_combination():
    combo = RuleItem(id=1, brand="Combo", generic="paracetamol + diclofenac",
                     drug_class="analgesic-paracetamol + NSAID", prescriber="x")
    fs = run_rules([combo], 70, load_rule_tables(), TODAY)
    [f] = [f for f in fs if f.code == "BEERS_65"]
    assert f.meta["target"] == "class:nsaid" and "(diclofenac)" in f.evidence
