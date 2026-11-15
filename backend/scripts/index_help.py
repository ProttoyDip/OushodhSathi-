"""Build or refresh Sathi's vector index of the app guide (docs/help/*.md).

  python scripts/index_help.py            # the database in DATABASE_URL (Postgres + pgvector) or local SQLite
  python scripts/index_help.py --dry-run  # show what would be embedded, call nothing

Only chunks whose content_hash changed are re-embedded, so re-running is cheap. Needs NVIDIA_API_KEY.
Run it after editing the guide; the API never embeds the guide per request.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import main  # noqa: E402,F401  (loads backend/.env)
from app import embeddings, help_vectors  # noqa: E402
from app.store import Store  # noqa: E402


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    store = Store()
    where = "Postgres" if store.pg else f"SQLite ({store.path})"
    chunks = help_vectors.chunks()
    if args.dry_run:
        help_vectors.ensure_table(store)
        have = help_vectors.stored_hashes(store)
        changed = [c for c in chunks if have.get((c.id, c.lang)) != c.content_hash()]
        print(f"{where}: {len(chunks)} chunks, {len(changed)} would be embedded with {embeddings.MODEL}")
        sys.exit(0)
    if not embeddings.configured():
        sys.exit("NVIDIA_API_KEY is not set: nothing to embed (Sathi keeps using keyword search)")
    print(f"{where}: {help_vectors.build_index(store)} (model {embeddings.MODEL}, {embeddings.DIM} dimensions)")
