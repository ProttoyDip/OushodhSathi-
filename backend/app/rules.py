"""Deterministic safety rules. Pure functions: no I/O, no AI, no randomness.

This is the ONLY place safety flags are created (AGENTS.md rule 1).
"""
from __future__ import annotations

import calendar
import hashlib
import re
from collections import defaultdict
from datetime import date
from itertools import combinations

from rapidfuzz.distance import JaroWinkler

from .kidney import KidneyContext, kdigo_stage
from .models import Flag, RuleItem
from .tables import BeersRow, InteractionRow, RenalRow, RuleTables

EXPIRY_WARNING_DAYS = 30
BEERS_AGE = 65
ACB_THRESHOLD = 3          # total ACB score >= 3 is clinically significant
LOOK_ALIKE_SIMILARITY = 0.85  # Jaro-Winkler on cleaned brand names (weights a shared start)
LOOK_ALIKE_PREFIX = 2          # ...and the names must start with the same letters
SOUND_ALIKE_MIN_LEN = 4    # shorter names give too many phonetic collisions


def _key(*parts: str) -> str:
    """Stable flag key: the same finding on a re-run gets the same key."""
    raw = "|".join(p.lower() for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _generics(item: RuleItem) -> list[str]:
    """Combination products ("a + b") are checked component by component."""
    if not item.generic:
        return []
    return [g.strip().lower() for g in item.generic.split("+") if g.strip()]


def _components(item: RuleItem) -> list[tuple[str, str]]:
    """(generic, class) for each active ingredient of a fixed-dose combination.

    "amlodipine + atenolol" with "CCB-dihydropyridine + beta-blocker" pairs by position.
    A single class for several generics applies to all of them; otherwise unknown ("").
    """
    generics = _generics(item)
    classes = [c.strip().lower() for c in (item.drug_class or "").split("+") if c.strip()]
    if len(classes) == len(generics):
        return list(zip(generics, classes))
    shared = classes[0] if len(classes) == 1 else ""
    return [(g, shared) for g in generics]


def _hits(target: str, generic: str, cls: str) -> bool:
    """Does a table target ("class:NSAID" or a generic name) match one ingredient?"""
    if target.startswith("class:"):
        return cls == target[6:]
    return target == generic


def _label(item: RuleItem) -> str:
    return f"{item.brand} {item.strength}".strip() if item.strength else item.brand


def _expiry_end(expiry: str) -> date | None:
    """'YYYY-MM' -> last day of that month (strips are good until month end)."""
    try:
        year, month = (int(x) for x in expiry.strip()[:7].split("-"))
        return date(year, month, calendar.monthrange(year, month)[1])
    except (ValueError, AttributeError):
        return None


def duplicate_generic(items: list[RuleItem]) -> list[Flag]:
    by_generic: dict[str, list[RuleItem]] = defaultdict(list)
    for it in items:
        for g in _generics(it):
            by_generic[g].append(it)
    flags = []
    for generic, group in sorted(by_generic.items()):
        brands = {it.brand.lower() for it in group}
        prescribers = {(it.prescriber or "").lower() for it in group}
        if len(group) < 2 or (len(brands) < 2 and len(prescribers) < 2):
            continue
        names = " and ".join(_label(it) for it in group)
        sources = sorted({it.prescriber for it in group if it.prescriber})
        from_ = f" (from {', '.join(sources)})" if sources else ""
        flags.append(Flag(
            key=_key("DUPLICATE_GENERIC", generic, *sorted(brands)),
            code="DUPLICATE_GENERIC", severity="red", routed_to="doctor",
            item_ids=sorted(it.id for it in group),
            evidence=f"{names}{from_} {'both' if len(group) == 2 else 'all'} contain {generic}. The patient may be taking a double dose.",
            data_source="brand table",
            meta={"generic": generic},
        ))
    return flags


def therapeutic_duplication(items: list[RuleItem], duplicate_classes: frozenset[str]) -> list[Flag]:
    by_class: dict[str, dict[int, tuple[RuleItem, str]]] = defaultdict(dict)
    for it in items:
        for generic, cls in _components(it):
            if cls in duplicate_classes:
                by_class[cls][it.id] = (it, generic)
    flags = []
    for cls, members in sorted(by_class.items()):
        group = [it for it, _ in members.values()]
        generics = sorted({g for _, g in members.values()})
        if len(generics) < 2:
            continue  # same generic twice is DUPLICATE_GENERIC, not this rule
        names = ", ".join(f"{_label(it)} ({g})" for it, g in members.values())
        display_cls = next((c for it in group for g, c in zip(_generics(it), (it.drug_class or "").split("+"))
                            if c.strip().lower() == cls), cls).strip()
        flags.append(Flag(
            key=_key("THERAPEUTIC_DUPLICATION", cls, *generics),
            code="THERAPEUTIC_DUPLICATION", severity="amber", routed_to="pharmacist",
            item_ids=sorted(it.id for it in group),
            evidence=f"{names} are different medicines from the same class ({display_cls}). Usually only one is needed.",
            data_source="duplicate_classes.txt",
            meta={"drug_class": display_cls, "generics": generics},
        ))
    return flags


def interactions(items: list[RuleItem], table: tuple[InteractionRow, ...]) -> list[Flag]:
    """One flag per pair of generics (two strips of the same drug share the flag),
    keeping the most severe matching row."""
    rank = {"major": 2, "moderate": 1}
    best: dict[tuple[str, str], tuple[InteractionRow, dict[int, RuleItem]]] = {}
    for x, y in combinations(items, 2):
        for gx, cx in _components(x):
            for gy, cy in _components(y):
                if gx == gy:
                    continue  # the same ingredient twice is DUPLICATE_GENERIC
                for row in table:
                    if row.severity not in rank:
                        continue
                    if (_hits(row.a, gx, cx) and _hits(row.b, gy, cy)) or (_hits(row.a, gy, cy) and _hits(row.b, gx, cx)):
                        pair = tuple(sorted((gx, gy)))
                        current = best.get(pair)
                        if current is None or rank[row.severity] > rank[current[0].severity]:
                            members = current[1] if current else {}
                            best[pair] = (row, members)
                        best[pair][1].update({x.id: x, y.id: y})
    flags = []
    for pair, (row, members) in sorted(best.items()):
        group = sorted(members.values(), key=lambda it: it.id)
        major = row.severity == "major"
        sides = [[it for it in group if g in _generics(it)] for g in pair]
        describe = [" / ".join(_label(it) for it in side) + f" ({g})" for side, g in zip(sides, pair) if side]
        flags.append(Flag(
            key=_key("INTERACTION", row.a, row.b, *pair),
            code="INTERACTION",
            severity="red" if major else "amber",
            routed_to="doctor" if major else "pharmacist",
            item_ids=[it.id for it in group],
            evidence=f"{' with '.join(describe)}: {row.severity} interaction. {row.effect}",
            data_source=row.source,
            meta={"interaction_severity": row.severity, "effect": row.effect, "effect_bn": row.effect_bn},
        ))
    return flags


def beers(items: list[RuleItem], age: int | None, table: tuple[BeersRow, ...]) -> list[Flag]:
    if age is None or age < BEERS_AGE:
        return []
    hits: dict[str, tuple[BeersRow, str, list[RuleItem]]] = {}
    for it in items:
        for generic, cls in _components(it):
            for row in table:
                if _hits(row.target, generic, cls):
                    entry = hits.setdefault(row.target + "|" + generic, (row, generic, []))
                    if it not in entry[2]:
                        entry[2].append(it)
                    break
    flags = []
    for _, (row, generic, group) in sorted(hits.items()):
        names = " and ".join(_label(it) for it in group)
        flags.append(Flag(
            key=_key("BEERS_65", row.target, generic, *sorted(it.brand for it in group)),
            code="BEERS_65", severity="amber", routed_to="pharmacist",
            item_ids=sorted(it.id for it in group),
            evidence=f"{names} ({generic}): listed in the AGS Beers Criteria for adults 65+. {row.reason}",
            data_source="AGS Beers Criteria (beers_seed.csv)",
            meta={"target": row.target, "recommendation": row.recommendation, "reason_bn": row.reason_bn},
        ))
    return flags


def expired(items: list[RuleItem], today: date) -> list[Flag]:
    flags = []
    for it in items:
        end = _expiry_end(it.expiry) if it.expiry else None
        if end is None:
            continue
        days_left = (end - today).days
        if days_left < 0:
            severity, text = "red", f"{_label(it)} expired at the end of {it.expiry}."
        elif days_left <= EXPIRY_WARNING_DAYS:
            severity, text = "amber", f"{_label(it)} expires at the end of {it.expiry} ({days_left} days left)."
        else:
            continue
        flags.append(Flag(
            key=_key("EXPIRED", severity, it.brand, it.strength or "", it.expiry or ""),
            code="EXPIRED", severity=severity, routed_to="pharmacist",
            item_ids=[it.id], evidence=text, data_source="printed expiry date",
            meta={"expiry": it.expiry, "days_left": days_left},
        ))
    return flags


def anticholinergic_burden(items: list[RuleItem], age: int | None, acb: dict[str, int]) -> list[Flag]:
    """Sum the Anticholinergic Cognitive Burden (ACB) score of every distinct generic.

    A total of 3 or more in an adult 65+ is linked to confusion, falls and cognitive
    decline. One flag for the whole list, routed to the pharmacist.
    """
    if age is None or age < BEERS_AGE or not acb:
        return []
    scored: dict[str, int] = {}
    members: dict[int, RuleItem] = {}
    for it in items:
        for g in _generics(it):
            if g in acb:
                scored[g] = acb[g]
                members[it.id] = it
    total = sum(scored.values())
    if total < ACB_THRESHOLD:
        return []
    group = sorted(members.values(), key=lambda it: it.id)
    parts = ", ".join(f"{g} {s}" for g, s in sorted(scored.items(), key=lambda kv: (-kv[1], kv[0])))
    return [Flag(
        key=_key("ANTICHOLINERGIC_BURDEN", *sorted(scored)),
        code="ANTICHOLINERGIC_BURDEN", severity="amber", routed_to="pharmacist",
        item_ids=[it.id for it in group],
        evidence=(f"Anticholinergic burden score {total} ({parts}) from "
                  f"{' and '.join(_label(it) for it in group)}. A total of {ACB_THRESHOLD} or more in adults 65+ "
                  "is linked to confusion, falls and memory problems."),
        data_source="Anticholinergic Cognitive Burden scale, 2012 update (acb_seed.csv)",
        meta={"score": total, "scores": scored, "threshold": ACB_THRESHOLD},
    )]


_FORM_WORDS = re.compile(r"\b(tab|tablet|cap|capsule|syrup|susp|inj|injection|cream|drop|drops|xr|sr|er|mr|ds)\b")


def _clean_name(brand: str) -> str:
    """Brand name for comparison: lowercase letters only, no strengths or dosage forms."""
    name = _FORM_WORDS.sub(" ", re.sub(r"[0-9.]+\s*(mg|mcg|g|ml|iu|%)?", " ", brand.lower()))
    return re.sub(r"[^a-z]", "", name)


def _sound_key(name: str) -> str:
    """A small phonetic key: how the name sounds when read aloud (Bangla or English speakers)."""
    if not name:
        return ""
    s = re.sub(r"c(?=[eiy])", "s", name)  # soft c: "Ceclo" sounds like "Seclo"
    for a, b in (("ph", "f"), ("ck", "k"), ("qu", "k"), ("q", "k"), ("c", "k"), ("x", "ks"),
                 ("z", "s"), ("v", "b"), ("w", "b"), ("th", "t"), ("dh", "d"), ("bh", "b"), ("kh", "k"),
                 ("gh", "g"), ("sh", "s"), ("y", "i")):
        s = s.replace(a, b)
    head, tail = s[0], re.sub(r"[aeiou]", "", s[1:])
    return re.sub(r"(.)\1+", r"\1", head + tail)


def look_alike_names(items: list[RuleItem]) -> list[Flag]:
    """Two brands in the same house whose names look or sound alike but contain
    different medicines: an elderly patient (or a shopkeeper) can mix them up."""
    flags = []
    seen: set[tuple[str, str]] = set()
    for x, y in combinations(items, 2):
        gx, gy = set(_generics(x)), set(_generics(y))
        if not gx or not gy or gx & gy:
            continue  # unknown medicine, or the same medicine (other rules cover that)
        nx, ny = _clean_name(x.brand), _clean_name(y.brand)
        if not nx or not ny or nx == ny:
            continue
        pair = tuple(sorted((nx, ny)))
        if pair in seen:
            continue
        similarity = JaroWinkler.similarity(nx, ny)
        looks = similarity >= LOOK_ALIKE_SIMILARITY and nx[:LOOK_ALIKE_PREFIX] == ny[:LOOK_ALIKE_PREFIX]
        sounds = min(len(nx), len(ny)) >= SOUND_ALIKE_MIN_LEN and _sound_key(nx) == _sound_key(ny)
        if not looks and not sounds:
            continue
        seen.add(pair)
        ratio = similarity * 100
        how = "look and sound alike" if looks and sounds else ("sound alike" if sounds else "look alike")
        flags.append(Flag(
            key=_key("LOOK_ALIKE_NAMES", *pair),
            code="LOOK_ALIKE_NAMES", severity="amber", routed_to="pharmacist",
            item_ids=sorted((x.id, y.id)),
            evidence=(f"{_label(x)} ({' + '.join(sorted(gx))}) and {_label(y)} ({' + '.join(sorted(gy))}) "
                      f"have names that {how} (similarity {round(ratio)}%) but are different medicines. "
                      "They are easy to mix up at home or at the shop."),
            data_source="name similarity (Jaro-Winkler + phonetic key)",
            meta={"similarity": round(ratio, 1), "looks_alike": looks, "sound_alike": sounds, "how": how},
        ))
    return flags


TRIPLE_WHAMMY_GROUPS = ("raas", "diuretic", "nsaid")
TRIPLE_WHAMMY_SOURCE = (
    # An ACE inhibitor or ARB + a diuretic + an NSAID together: a recognised cause of acute
    # kidney injury, especially in older adults.
    # - Medsafe NZ, "NSAIDs and Acute Kidney Injury" (2013):
    #   https://medsafe.govt.nz/profs/puarticles/june2013nsaids.htm
    # - Lapi F et al., BMJ 2013;346:e8525 (nested case-control; triple therapy RR 1.31 vs double)
    # - Harężlak T et al., Adv Ther 2022, "Drug Interactions Affecting Kidney Function: Beware of
    #   Health Threats from Triple Whammy": https://doi.org/10.1007/s12325-021-01939-9
    "Medsafe NZ 2013 (NSAIDs and AKI); Lapi et al., BMJ 2013;346:e8525; Harężlak et al., Adv Ther 2022 "
    "(class_groups.csv)"
)


def triple_whammy(items: list[RuleItem], groups: dict[str, frozenset[str]]) -> list[Flag]:
    """RAAS blocker (ACE inhibitor or ARB) + diuretic + NSAID in the same house.

    Combination products count ingredient by ingredient, so Osartil Plus (losartan +
    hydrochlorothiazide) covers both RAAS and diuretic. One flag per household. The pairwise
    NSAID + ARB interaction stays a separate finding.
    """
    if not groups or any(g not in groups for g in TRIPLE_WHAMMY_GROUPS):
        return []
    found: dict[str, dict[str, RuleItem]] = {g: {} for g in TRIPLE_WHAMMY_GROUPS}
    members: dict[int, RuleItem] = {}
    for it in items:
        for generic, cls in _components(it):
            for g in TRIPLE_WHAMMY_GROUPS:
                if cls and cls in groups[g]:
                    found[g][generic] = it
                    members[it.id] = it
    if not all(found[g] for g in TRIPLE_WHAMMY_GROUPS):
        return []
    group_items = sorted(members.values(), key=lambda it: it.id)
    named = {g: sorted(found[g]) for g in TRIPLE_WHAMMY_GROUPS}
    describe = "; ".join(
        f"{label}: {', '.join(f'{_label(found[g][gen])} ({gen})' for gen in named[g])}"
        for g, label in zip(TRIPLE_WHAMMY_GROUPS, ("blood-pressure medicine (ACE inhibitor/ARB)", "diuretic", "NSAID"))
    )
    return [Flag(
        key=_key("TRIPLE_WHAMMY", *sorted(g for gens in named.values() for g in gens)),
        code="TRIPLE_WHAMMY", severity="red", routed_to="doctor",
        item_ids=[it.id for it in group_items],
        evidence=(f"{describe}. An ACE inhibitor or ARB, a diuretic and an NSAID taken together "
                  "(the \"triple whammy\") can cause acute kidney injury, especially in older adults."),
        data_source=TRIPLE_WHAMMY_SOURCE,
        meta=named,
    )]


KIDNEY_TEST_MAX_DAYS = 365
# FDA Drug Safety Communication, 8 Apr 2016 (metformin): "obtain an eGFR at least annually":
# https://www.fda.gov/drugs/drug-safety-and-availability/fda-drug-safety-communication-fda-revises-warnings-regarding-use-diabetes-medicine-metformin-certain
KIDNEY_TEST_DUE_GENERICS = ("metformin",)
KIDNEY_TEST_SOURCE = "FDA Drug Safety Communication on metformin, 8 Apr 2016 (eGFR at least annually)"


def kidney_dose(items: list[RuleItem], kidney: KidneyContext | None, table: tuple[RenalRow, ...]) -> list[Flag]:
    """A medicine that needs care at the household's latest eGFR (renal_seed.csv).
    One flag per (generic, band); when several bands match, the lowest threshold wins."""
    if kidney is None or kidney.egfr is None or not table:
        return []
    egfr = kidney.egfr
    hits: dict[str, tuple[RenalRow, list[RuleItem]]] = {}
    for it in items:
        for generic, cls in _components(it):
            for row in table:
                if _hits(row.target, generic, cls) and egfr < row.egfr_below:
                    current = hits.get(generic)
                    if current is None or row.egfr_below < current[0].egfr_below:
                        hits[generic] = (row, current[1] if current else [])
                    if it not in hits[generic][1]:
                        hits[generic][1].append(it)
    flags = []
    when = kidney.taken_on.isoformat() if kidney.taken_on else "unknown date"
    for generic, (row, group) in sorted(hits.items()):
        flags.append(Flag(
            key=_key("KIDNEY_DOSE", generic, f"{row.egfr_below:g}"),
            code="KIDNEY_DOSE", severity=row.severity, routed_to=row.routed_to,
            item_ids=sorted(it.id for it in group),
            evidence=(f"{' and '.join(_label(it) for it in group)} ({generic}): eGFR {egfr:.0f} mL/min/1.73 m² "
                      f"({kdigo_stage(egfr)}, creatinine test of {when}) is below {row.egfr_below:g}. {row.note}"),
            data_source=row.source,
            meta={"egfr": round(egfr, 1), "stage": kdigo_stage(egfr), "taken_on": when,
                  "threshold": row.egfr_below, "generic": generic, "note_bn": row.note_bn},
        ))
    return flags


def kidney_test_due(items: list[RuleItem], kidney: KidneyContext | None, today: date) -> list[Flag]:
    """Metformin in the house and no kidney test in the last year (or never)."""
    if kidney is None:
        return []
    group = [it for it in items if any(g in KIDNEY_TEST_DUE_GENERICS for g in _generics(it))]
    if not group:
        return []
    if kidney.taken_on is not None and (today - kidney.taken_on).days <= KIDNEY_TEST_MAX_DAYS:
        return []
    last = f"the last kidney test was on {kidney.taken_on.isoformat()}" if kidney.taken_on else "no kidney test is recorded"
    generics = sorted({g for it in group for g in _generics(it) if g in KIDNEY_TEST_DUE_GENERICS})
    return [Flag(
        key=_key("KIDNEY_TEST_DUE", *generics),
        code="KIDNEY_TEST_DUE", severity="amber", routed_to="pharmacist",
        item_ids=sorted(it.id for it in group),
        evidence=(f"{' and '.join(_label(it) for it in group)} ({', '.join(generics)}): {last}. "
                  "Kidney function (eGFR) should be checked at least once a year."),
        data_source=KIDNEY_TEST_SOURCE,
        meta={"last_test": kidney.taken_on.isoformat() if kidney.taken_on else None, "generics": generics},
    )]


SEVERITY_ORDER = {"red": 0, "amber": 1}


def run_rules(items: list[RuleItem], age: int | None, tables: RuleTables, today: date,
              kidney: KidneyContext | None = None) -> list[Flag]:
    """Run every rule on the confirmed items. Red first, then by code.
    kidney: the household's latest kidney test; None skips the kidney rules (unknown context)."""
    flags = (
        duplicate_generic(items)
        + therapeutic_duplication(items, tables.duplicate_classes)
        + interactions(items, tables.interactions)
        + beers(items, age, tables.beers)
        + expired(items, today)
        + anticholinergic_burden(items, age, tables.acb)
        + look_alike_names(items)
        + triple_whammy(items, tables.class_groups)
        + kidney_dose(items, kidney, tables.renal)
        + kidney_test_due(items, kidney, today)
    )
    unique = {f.key: f for f in flags}  # belt and braces: never two flags with one key
    return sorted(unique.values(), key=lambda f: (SEVERITY_ORDER[f.severity], f.code, f.item_ids))
