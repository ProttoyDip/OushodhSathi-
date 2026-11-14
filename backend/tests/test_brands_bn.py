"""Brand names written in Bangla script (handwritten prescriptions, shop labels)."""
from app.brands import match_brand, normalise_bn
from app.tables import load_brands


def test_bangla_brand_matches_exactly_with_strength_and_form_removed():
    for text in ("নাপা", "নাপা ৫০০ মিগ্রা", "নাপা 500 mg ট্যাবলেট"):
        m = match_brand(text)
        assert (m.match_method, m.generic) == ("exact", "paracetamol"), text


def test_bangla_combination_brand_is_not_collapsed_to_the_single_brand():
    m = match_brand("নাপা এক্সট্রা")
    assert m.row.brand == "Napa Extra" and m.generic == "paracetamol + caffeine"
    assert match_brand("এমডোকাল প্লাস").row.brand == "Amdocal Plus"


def test_spelling_variants_match_fuzzily():
    m = match_brand("কামলোডিন")  # ক্যা written as কা
    assert m.match_method == "fuzzy" and m.row.brand == "Camlodin"
    assert match_brand("অ্যানজিলোক").row.brand == "Angilock"


def test_cut_off_fragment_is_never_guessed():
    assert match_brand("নাপ").match_method == "not_found"
    assert match_brand("ক্যাম").match_method == "not_found"


def test_unknown_bangla_text_is_not_found():
    assert match_brand("প্যারাসিটামল").match_method == "not_found"  # a generic, not a brand
    assert match_brand("১০০ মিগ্রা").match_method == "not_found"


def test_bangla_vowel_signs_survive_normalisation():
    assert normalise_bn("ক্যামলোডিন ৫ মিগ্রা") == "ক্যামলোডিন"


def test_every_alias_points_at_a_brand_in_the_table():
    import csv

    from app.brands import normalise
    from app.tables import DATA_DIR
    known = {normalise(r.brand) for r in load_brands().values()}
    with (DATA_DIR / "brands_bn.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            assert normalise(r["brand"]) in known, r
            assert match_brand(r["bn"]).row.brand == r["brand"], r


def test_latin_names_are_unchanged():
    assert match_brand("Napa 500 mg").match_method == "exact"
    assert match_brand("Napa Extra").row.brand == "Napa Extra"
