"""Seeds the invented demo household (Rahima Begum, 68). Used by scripts/seed_demo.py and
by POST /demo/reset, so every judge starts from the same fresh state in about a second.

Modes:
  judge    (default) both views have something to show: the paracetamol duplicate and the
           diclofenac + losartan interaction are confirmed with notes (the family sees them);
           the amlodipine duplicate, the clonazepam + amitriptyline interaction, the expired
           amitriptyline and the rest stay pending in the reviewer's queue.
  pending  every finding waits for the reviewer.
  reviewed every finding is confirmed.

Confirmations use the fixed, pre-reviewed Bangla templates (no model call): fast and
the same every time. Safety flags still come only from rules.py.
"""
from __future__ import annotations

import secrets
from datetime import date
from typing import Literal

from .agent import resolve_brand
from .demo import DEMO_ALLERGIES, DEMO_BP, DEMO_CONTACT, DEMO_ITEMS, DEMO_NOTES, DEMO_PATIENT, DEMO_PURPOSE, demo_bp_dates
from .explain import template
from .models import ReviewIn, RuleItem
from .rules import run_rules
from .store import Store, now
from .tables import load_rule_tables

Mode = Literal["judge", "pending", "reviewed"]
DEMO_REVIEWER = "Demo pharmacist (invented)"

# judge mode: which findings arrive already confirmed, by rule and the brands involved
JUDGE_CONFIRMED = {
    ("DUPLICATE_GENERIC", frozenset({"Napa", "Ace"})):
        "Both strips are paracetamol. Please bring both strips to the next visit so we can decide together.",
    ("INTERACTION", frozenset({"Clofenac", "Angilock"})):
        "Diclofenac can weaken losartan's effect on blood pressure and strain the kidneys. I have flagged this for Dr. A to review at the next visit.",
}


def demo_patient_id(store: Store) -> int | None:
    found = [p for p in store.list_patients() if p.is_demo and p.name == DEMO_PATIENT.name]
    return found[0].id if found else None


def seed_demo(store: Store, mode: Mode = "judge") -> dict:
    pid = demo_patient_id(store)
    if pid is None:
        pid = store.create_patient(DEMO_PATIENT).id
    else:
        store.reset_household(pid)

    for it in DEMO_ITEMS:
        store.add_item(pid, it, **resolve_brand(it.brand, it.strength, store),
                       prompt_version="demo-seed", model_id="demo (no model called)", confirmed=True)
    for day, (sys_, dia) in zip(demo_bp_dates(date.today()), DEMO_BP):
        store.add_bp(pid, day, sys_, dia)
    # what the demo pharmacist already did: purposes, approved times, allergy confirmed
    ts = now()
    for it in store.list_items(pid):
        purpose, purpose_bn = DEMO_PURPOSE.get(it.brand, (None, None))
        store.update_item(it.id, purpose=purpose, purpose_bn=purpose_bn,
                          schedule_approved_by=DEMO_REVIEWER, schedule_approved_at=ts)
    store.update_patient(pid, allergies=DEMO_ALLERGIES, allergies_confirmed_by=DEMO_REVIEWER,
                         allergies_confirmed_at=ts, emergency_contact_name=DEMO_CONTACT[0],
                         emergency_contact_phone=DEMO_CONTACT[1])
    if not store.emergency_token(pid):
        store.update_patient(pid, emergency_token=secrets.token_urlsafe(18))

    # the rules engine makes every finding; the demo pharmacist confirms some of them
    patient = store.get_patient(pid)
    items = store.list_items(pid, confirmed_only=True)
    by_id = {it.id: it for it in items}
    rule_items = [RuleItem(**it.model_dump(include=set(RuleItem.model_fields))) for it in items]
    stored = store.sync_flags(pid, run_rules(rule_items, patient.age, load_rule_tables(), date.today()))
    store.mark_checked(pid)
    store.log_activity(pid, "scanned", len(items))
    store.log_activity(pid, "sent_for_review", len(items))
    confirmed = 0
    for f in stored:
        brands = frozenset(by_id[i].brand for i in f.item_ids if i in by_id)
        note = None
        if mode == "reviewed":
            note = DEMO_NOTES.get(f"{f.code}:{f.meta.get('generic', '')}", "Reviewed. We will discuss this at the next visit.")
        elif mode == "judge":
            note = JUDGE_CONFIRMED.get((f.code, brands))
        if note is None:
            continue
        flag_items = [by_id[i] for i in f.item_ids if i in by_id]
        explanation = template(f.model_copy(update={"status": "confirmed"}), flag_items)
        store.review_flag(f.id, ReviewIn(status="confirmed", reviewer=DEMO_REVIEWER, note=note), explanation)
        confirmed += 1
    if confirmed:
        store.log_activity(pid, "finding_confirmed", confirmed)
    store.log_activity(pid, "schedule_approved", len(items))
    return {"patient_id": pid, "items": len(items), "flags": len(stored), "confirmed": confirmed,
            "pending": len(stored) - confirmed, "mode": mode}
