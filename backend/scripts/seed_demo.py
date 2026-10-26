"""Create the demo household (Rahima Begum, 68 — invented data).

Usage:
  python scripts/seed_demo.py              # items confirmed, rules run, flags pending review
  python scripts/seed_demo.py --reviewed   # also confirms every flag with demo clinician notes
  python scripts/seed_demo.py --reset      # delete the database first
  python scripts/seed_demo.py --if-empty   # only seed when there are no patients (used on deploy)
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import main  # noqa: E402  (loads .env)
from app.demo import DEMO_BP, DEMO_ITEMS, DEMO_NOTES, DEMO_PATIENT, demo_bp_dates  # noqa: E402
from app.models import ReviewIn  # noqa: E402
from app.store import Store  # noqa: E402

DEMO_REVIEWER = "Demo pharmacist (invented)"


def seed(store: Store, reviewed: bool = False) -> int:
    existing = [p for p in store.list_patients() if p.is_demo and p.name == DEMO_PATIENT.name]
    patient = existing[0] if existing else store.create_patient(DEMO_PATIENT)
    store.clear_items(patient.id)
    for it in DEMO_ITEMS:
        store.add_item(patient.id, it, **main.resolve_brand(it.brand, it.strength, store),
                       prompt_version="demo-seed", model_id="demo (no model called)", confirmed=True)
    if not store.list_bp(patient.id):
        for day, (sys_, dia) in zip(demo_bp_dates(date.today()), DEMO_BP):
            store.add_bp(patient.id, day, sys_, dia)
    result = main.run_check(patient.id, store)
    if reviewed:
        for f in store.list_flags(patient.id, statuses=("pending_review",)):
            note = DEMO_NOTES.get(f"{f.code}:{f.meta.get('generic', '')}",
                                  "Reviewed. We will discuss this at the next visit.")
            main.review_flag(f.id, ReviewIn(status="confirmed", reviewer=DEMO_REVIEWER, note=note), store)
    print(f"Demo patient id={patient.id}: {len(DEMO_ITEMS)} items, {result['flags_total']} flags "
          f"({'confirmed' if reviewed else 'pending review'})")
    return patient.id


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviewed", action="store_true")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--if-empty", action="store_true")
    args = ap.parse_args()
    store = Store()
    if args.if_empty and store.list_patients():
        print("Database already has patients; not seeding.")
        sys.exit(0)
    if args.reset:
        store.db.close()
        Path(store.path).unlink(missing_ok=True)
        store = Store()
    seed(store, reviewed=args.reviewed)
