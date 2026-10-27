"""Same medicine, lower price: other brands of the SAME generic(s), strength and form.

Never switches anything. A brand change happens only if the pharmacist or doctor approves
it; the family gets a question they can send, and a fixed notice saying exactly that.
Prices are demo reference prices from brands_seed.csv ("verify MRP"), not live MRPs.
"""
from __future__ import annotations

import re

from .models import MedicineItem
from .refills import counts
from .tables import BrandRow, load_brands

NOTICE_BN = "আপনার ফার্মাসিস্ট বা ডাক্তারকে জিজ্ঞেস করুন — ডাক্তার বা ফার্মাসিস্টের অনুমোদন ছাড়া ব্র্যান্ড পরিবর্তন করবেন না।"
NOTICE_EN = "Ask your pharmacist or doctor — do not change the brand without their approval."
DAYS_PER_MONTH = 30
DAYS_PER_YEAR = 365


def norm_strength(s: str | None) -> str:
    """'500 mg' == '500mg' == '500 MG'; '5 mg + 25 mg' keeps its parts in order."""
    return re.sub(r"\s+", "", (s or "").lower())


def _ingredients(generic: str | None) -> tuple[str, ...]:
    return tuple(sorted(g.strip().lower() for g in (generic or "").split("+") if g.strip()))


def same_product(row: BrandRow, generics: tuple[str, ...], strength: str, form: str) -> bool:
    return (_ingredients(row.generic) == generics and norm_strength(row.strength) == strength
            and row.form == form)


def find_savings(items: list[MedicineItem], duplicate_ids: set[int]) -> dict:
    """`duplicate_ids`: items in an open duplicate finding. Those wait for the reviewer's
    decision first, so no price suggestion is made for them."""
    table = load_brands()
    rows = []
    for it in items:
        if not counts(it) or it.id in duplicate_ids or not it.schedule_approved_at or not it.doses_per_day:
            continue
        own = table.get(it.brand.lower())
        if own is None or own.mrp_bdt is None:
            continue
        generics = _ingredients(it.generic or own.generic)
        strength = norm_strength(it.strength or own.strength)
        form = (it.form or own.form).lower()
        if not same_product(own, generics, strength, form):
            continue  # this pack's reference price is for another strength or form
        cheaper = [r for r in table.values()
                   if r.brand.lower() != own.brand.lower() and r.mrp_bdt is not None and r.mrp_bdt < own.mrp_bdt
                   and same_product(r, generics, strength, form)]
        if not cheaper:
            continue
        best = min(cheaper, key=lambda r: (r.mrp_bdt, r.brand))
        per_day = it.doses_per_day * max(it.per_dose, 1)
        diff = own.mrp_bdt - best.mrp_bdt
        rows.append({
            "item_id": it.id, "brand": it.brand, "generic": it.generic or own.generic, "strength": it.strength or own.strength,
            "form": form, "tablets_per_day": per_day, "current_mrp_bdt": own.mrp_bdt,
            "alternative": {"brand": best.brand, "mrp_bdt": best.mrp_bdt, "pack_source": best.pack_source},
            "monthly_bdt": round(diff * per_day * DAYS_PER_MONTH),
            "yearly_bdt": round(diff * per_day * DAYS_PER_YEAR),
        })
    rows.sort(key=lambda r: -r["yearly_bdt"])
    return {
        "items": rows,
        "total_monthly_bdt": sum(r["monthly_bdt"] for r in rows),
        "total_yearly_bdt": sum(r["yearly_bdt"] for r in rows),
        "notice_bn": NOTICE_BN, "notice_en": NOTICE_EN,
        "price_note": "Demo reference prices — verify MRP with the pharmacy",
    }
