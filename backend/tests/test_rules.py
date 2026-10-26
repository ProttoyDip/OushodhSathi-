from datetime import date

from app.brands import match_brand
from app.models import RuleItem
from app.rules import run_rules
from app.tables import load_rule_tables

TODAY = date(2026, 10, 26)


def items(*specs):
    """specs: (brand, prescriber, expiry) tuples; generic/class come from the brand table."""
    out = []
    for i, spec in enumerate(specs, 1):
        brand, prescriber, expiry = (spec + (None, None))[:3]
        m = match_brand(brand)
        out.append(RuleItem(id=i, brand=brand, generic=m.generic, drug_class=m.drug_class,
                            prescriber=prescriber, expiry=expiry))
    return out


def run(age=50, *specs):
    return run_rules(items(*specs), age, load_rule_tables(), TODAY)


def codes(flags):
    return sorted((f.code, f.severity) for f in flags)


def test_napa_and_ace_give_one_red_duplicate_generic():
    flags = run(50, ("Napa", "drug shop"), ("Ace", "village doctor"))
    assert codes(flags) == [("DUPLICATE_GENERIC", "red")]
    assert flags[0].routed_to == "doctor"
    assert flags[0].meta["generic"] == "paracetamol"
    assert flags[0].item_ids == [1, 2]


def test_camlodin_and_amdocal_duplicate_generic():
    flags = run(50, ("Camlodin", "Dr. A"), ("Amdocal", "village doctor"))
    assert ("DUPLICATE_GENERIC", "red") in codes(flags)
    assert not any(f.code == "THERAPEUTIC_DUPLICATION" for f in flags)  # same generic is not "two drugs"


def test_seclo_and_maxpro_therapeutic_duplication():
    flags = run(50, ("Seclo",), ("Maxpro",))
    assert codes(flags) == [("THERAPEUTIC_DUPLICATION", "amber")]
    assert flags[0].routed_to == "pharmacist"
    assert flags[0].meta["drug_class"] == "PPI"


def test_rivotril_tryptin_major_interaction_and_beers_at_68():
    flags = run(68, ("Rivotril",), ("Tryptin",))
    assert ("INTERACTION", "red") in codes(flags)
    beers = [f for f in flags if f.code == "BEERS_65"]
    assert len(beers) == 2 and all(f.severity == "amber" for f in beers)


def test_no_beers_flags_under_65():
    flags = run(60, ("Rivotril",), ("Tryptin",))
    assert not any(f.code == "BEERS_65" for f in flags)


def test_clofenac_angilock_moderate_interaction():
    flags = run(50, ("Clofenac",), ("Angilock",))
    inter = [f for f in flags if f.code == "INTERACTION"]
    assert len(inter) == 1
    assert inter[0].severity == "amber" and inter[0].meta["interaction_severity"] == "moderate"


def test_expired_strip_is_red_and_near_expiry_is_amber():
    flags = run(50, ("Comet", None, "2026-09"), ("Atova", None, "2026-11"), ("Seclo", None, "2027-06"))
    exp = {f.item_ids[0]: f.severity for f in flags if f.code == "EXPIRED"}
    assert exp == {1: "red"}  # Atova: end of Nov is 35 days away, outside the 30-day window
    soon = run_rules(items(("Atova", None, "2026-11")), 50, load_rule_tables(), date(2026, 11, 5))
    assert [(f.code, f.severity) for f in soon] == [("EXPIRED", "amber")]


def test_napa_extra_does_not_fuzzy_match_napa():
    m = match_brand("Napa Extra")
    assert m.match_method == "not_found" and m.generic is None


def test_brand_normalisation_and_fuzzy():
    assert match_brand("NAPA 500 mg Tab").match_method == "exact"
    m = match_brand("Angiloc 50")  # one letter cut off the strip
    assert m.match_method == "fuzzy" and m.generic == "losartan" and m.match_score >= 88


def test_same_pair_never_flags_twice_for_same_reason():
    flags = run(68, ("Clofenac",), ("Angilock",), ("Clofenac",))
    keys = [f.key for f in flags]
    assert len(keys) == len(set(keys))
    assert sum(f.code == "BEERS_65" for f in flags) == 1
    inter = [f for f in flags if f.code == "INTERACTION"]
    assert len(inter) == 1 and inter[0].item_ids == [1, 2, 3]  # both Clofenac strips share one flag


def test_rules_are_deterministic():
    a = run(68, ("Napa",), ("Ace",), ("Rivotril",), ("Tryptin", None, "2026-09"))
    b = run(68, ("Napa",), ("Ace",), ("Rivotril",), ("Tryptin", None, "2026-09"))
    assert [f.model_dump() for f in a] == [f.model_dump() for f in b]
