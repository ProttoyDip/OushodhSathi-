"""Base generic names for the dataset brand list.

The full brand list (brands_full.csv) names generics as registered: "azithromycin dihydrate",
"esomeprazole magnesium trihydrate", "omeprazole (mups tablet)". The curated seed and every rule table
use the base name ("azithromycin"), and the rules compare names exactly, so without this Zimax
(azithromycin) and Azithrocin (azithromycin dihydrate) would not be seen as the same medicine.

Conservative by design: a salt word or an oral-form note is removed only when what is left is a generic
the app already knows (curated tables, or the same name listed bare in the dataset). "Potassium chloride"
stays as it is, and a topical, eye or injected form ("acyclovir (topical)") is never merged with tablets.
"""
from __future__ import annotations

import re

SALT_WORDS = frozenset("""
    hydrochloride dihydrochloride hcl hydrobromide hydrate monohydrate dihydrate trihydrate hemihydrate
    sesquihydrate anhydrous sodium potassium calcium magnesium maleate fumarate succinate tartrate
    bitartrate besilate besylate mesilate mesylate citrate phosphate sulphate sulfate bisulphate
    bisulfate acetate bromide nitrate oxalate malate lactate gluconate tromethamine trometamol
    usp bp inn
""".split())

# a parenthetical note that only says how a medicine taken by mouth is made
ORAL_NOTE = re.compile(r"\((?:[^()]*\b(?:oral|tablets?|capsules?|mups|sr|xr|er|dr|syrup|suspension|chewable)\b[^()]*)\)")


def _strip_salts(name: str, known: set[str]) -> str:
    words = name.split()
    while len(words) > 1 and words[-1] in SALT_WORDS:
        words = words[:-1]
        if " ".join(words) in known:
            return " ".join(words)
    return name


def _base_one(part: str, known: set[str]) -> str:
    part = " ".join(part.lower().split())
    if part in known:
        return part
    no_note = " ".join(ORAL_NOTE.sub(" ", part).split())
    if no_note != part and no_note in known:
        return no_note
    for candidate in (part, no_note):
        stripped = _strip_salts(candidate, known)
        if stripped in known:
            return stripped
    return part


def base_generic(generic: str, known: set[str]) -> str:
    """'azithromycin dihydrate' -> 'azithromycin' when 'azithromycin' is known; combinations part by part."""
    parts = [p for p in (generic or "").split("+") if p.strip()]
    return " + ".join(_base_one(p, known) for p in parts)
