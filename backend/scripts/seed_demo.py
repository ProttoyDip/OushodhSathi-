"""Create (or reset) the demo household (Rahima Begum, 68 — invented data).

Usage:
  python scripts/seed_demo.py              # judge mode: some findings confirmed, some pending review
  python scripts/seed_demo.py --pending    # every finding pending review
  python scripts/seed_demo.py --reviewed   # every finding confirmed with demo clinician notes
  python scripts/seed_demo.py --reset      # drop every table first (all households)
  python scripts/seed_demo.py --if-empty   # only seed when there are no patients (used on deploy)

The same seed runs behind POST /demo/reset (app/demo_seed.py).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import main  # noqa: E402,F401  (loads .env)
from app.demo_seed import seed_demo  # noqa: E402
from app.store import Store  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--reviewed", action="store_true")
    mode.add_argument("--pending", action="store_true")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--if-empty", action="store_true")
    args = ap.parse_args()
    store = Store()
    if args.if_empty and store.list_patients():
        print("Database already has patients; not seeding.")
        sys.exit(0)
    if args.reset:
        store.reset()
    r = seed_demo(store, "reviewed" if args.reviewed else "pending" if args.pending else "judge")
    print(f"Demo patient id={r['patient_id']}: {r['items']} items, {r['flags']} flags "
          f"({r['confirmed']} confirmed, {r['pending']} pending review) [{r['mode']}]")
