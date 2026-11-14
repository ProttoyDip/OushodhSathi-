"""Deterministic safety rules. Pure functions: no I/O, no AI, no randomness.

This is the ONLY place safety flags are created (AGENTS.md rule 1).
"""
from __future__ import annotations

import calendar
import hashlib
from collections import defaultdict
from datetime import date
from itertools import combinations

from .models import Flag, RuleItem
from .tables import BeersRow, InteractionRow, RuleTables

EXPIRY_WARNING_DAYS = 30
BEERS_AGE = 65


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


SEVERITY_ORDER = {"red": 0, "amber": 1}


def run_rules(items: list[RuleItem], age: int | None, tables: RuleTables, today: date) -> list[Flag]:
    """Run every rule on the confirmed items. Red first, then by code."""
    flags = (
        duplicate_generic(items)
        + therapeutic_duplication(items, tables.duplicate_classes)
        + interactions(items, tables.interactions)
        + beers(items, age, tables.beers)
        + expired(items, today)
    )
    unique = {f.key: f for f in flags}  # belt and braces: never two flags with one key
    return sorted(unique.values(), key=lambda f: (SEVERITY_ORDER[f.severity], f.code, f.item_ids))
