"""Base generic names: a salt or an oral-form note is removed only when the rest is a known generic."""
from app.generic_names import base_generic

KNOWN = {"azithromycin", "esomeprazole", "omeprazole", "acyclovir", "paracetamol", "caffeine", "potassium chloride"}


def test_salt_and_hydrate_words_are_removed_when_the_base_is_known():
    assert base_generic("azithromycin dihydrate", KNOWN) == "azithromycin"
    assert base_generic("esomeprazole magnesium trihydrate", KNOWN) == "esomeprazole"
    assert base_generic("omeprazole (mups tablet)", KNOWN) == "omeprazole"
    assert base_generic("paracetamol bp + caffeine", KNOWN) == "paracetamol + caffeine"


def test_unknown_bases_and_non_oral_forms_are_left_alone():
    assert base_generic("rupatadine fumarate", KNOWN) == "rupatadine fumarate"   # "rupatadine" is not known
    assert base_generic("potassium chloride", KNOWN) == "potassium chloride"      # the salt is the medicine
    assert base_generic("acyclovir (topical)", KNOWN) == "acyclovir (topical)"    # a cream is not a double dose
    assert base_generic("acyclovir (ophthalmic)", KNOWN) == "acyclovir (ophthalmic)"
