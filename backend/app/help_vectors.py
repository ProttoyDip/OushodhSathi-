"""Vector half of Sathi's hybrid app-guide retrieval: contextual chunks, an index, and search.

CONTEXTUAL CHUNKS (Anthropic, "Introducing Contextual Retrieval", 2024,
https://www.anthropic.com/news/contextual-retrieval): each guide entry in each language is one
chunk, and a short context header is prepended before it is embedded. Here the header is built
DETERMINISTICALLY from the guide's own structure (section, screen, and the entry's questions in
both languages), so no model is needed and the header is stored next to the chunk.

INDEX
- Postgres (Supabase): table help_chunks with a pgvector column vector(1024) and an HNSW index with
  cosine distance (vector_cosine_ops; operator <=>). Why HNSW and not IVFFlat: per the pgvector README
  (https://github.com/pgvector/pgvector), HNSW has no training step and can be created on an empty
  table, while IVFFlat should be built only after the table has data and needs re-building as it
  grows. For ~100 chunks an exact scan would also be instant; the index keeps the design right as the
  guide grows.
- SQLite (no DATABASE_URL): the same table with the vector stored as JSON text, searched in Python
  (unit vectors, so cosine = dot product; ~100 x 1024 multiplications per query).

scripts/index_help.py rebuilds the index and re-embeds only chunks whose content_hash changed. With
HELP_INDEX_ON_START=1 the API builds it once at start-up if the table is empty, never per request.
Without an NVIDIA key every function here returns nothing and retrieval is keyword-only, as before.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from dataclasses import dataclass

from . import embeddings
from .help_index import Entry, entries

log = logging.getLogger("oushodh.help_vectors")

# where each guide route lives, in words, for the context header
SCREENS = {
    "{home}": ("হোম পাতা", "home page"), "{home}/scan": ("ছবি তোলার পাতা", "scan screen"),
    "{home}/confirm": ("তালিকা মেলানোর পাতা", "confirm screen"), "{home}/status": ("যাচাইয়ের অবস্থা", "status screen"),
    "{home}/results": ("ফলাফলের পাতা", "results screen"), "{home}/report": ("সাপ্তাহিক রিপোর্ট", "weekly report"),
    "{home}/today": ("আজকের ওষুধ", "today's medicines"), "{home}/questions": ("ফার্মাসিস্টকে প্রশ্ন", "questions screen"),
    "{home}/visit": ("ডাক্তার দেখানোর আগে", "doctor visit page"), "{home}/cleanup": ("সরিয়ে রাখার তালিকা", "clean-up page"),
    "{home}/settings": ("সেটিংস", "settings"), "/passport/{id}": ("ওষুধের পাসপোর্ট", "medicine passport"),
    "/start": ("নতুন তালিকা", "start page"),
}

_store = None
_lock = threading.Lock()


@dataclass(frozen=True)
class Chunk:
    id: str
    lang: str
    header: str
    body: str

    @property
    def text(self) -> str:
        return f"{self.header}\n{self.body}"

    def content_hash(self, model: str = embeddings.MODEL) -> str:
        return hashlib.sha256(f"{model}|{self.text}".encode()).hexdigest()


def header_for(e: Entry, lang: str) -> str:
    """The deterministic context header: section, screen and the questions in both languages."""
    screen = SCREENS.get(e.route, (e.route, e.route))
    phr = " | ".join(e.phrasings)
    if lang == "bn":
        return (f"ওষুধসাথী অ্যাপের সহায়িকা। বিভাগ: {e.group['bn']} ({e.group['en']})। পাতা: {screen[0]}। "
                f"প্রশ্ন: {e.question['bn']} / {e.question['en']}। অন্যভাবে: {phr}")
    return (f"OushodhSathi app guide. Section: {e.group['en']} ({e.group['bn']}). Screen: {screen[1]}. "
            f"Question: {e.question['en']} / {e.question['bn']}. Also asked as: {phr}")


def chunks() -> list[Chunk]:
    return [Chunk(e.id, lang, header_for(e, lang), f"{e.question[lang]}\n{e.answer[lang]}")
            for e in entries().values() for lang in ("bn", "en")]


# ---- storage ---------------------------------------------------------------------------------

def ensure_table(store) -> bool:
    """Creates help_chunks. Returns False if pgvector is not available on this Postgres."""
    if store.pg:
        try:
            store._many([
                ("CREATE EXTENSION IF NOT EXISTS vector", ()),
                (f"CREATE TABLE IF NOT EXISTS help_chunks (id TEXT NOT NULL, lang TEXT NOT NULL, header TEXT NOT NULL, "
                 f"body TEXT NOT NULL, embedding vector({embeddings.DIM}) NOT NULL, model TEXT NOT NULL, "
                 "content_hash TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (id, lang))", ()),
                ("CREATE INDEX IF NOT EXISTS help_chunks_embedding_hnsw ON help_chunks "
                 "USING hnsw (embedding vector_cosine_ops)", ()),
            ])
            return True
        except Exception as e:  # noqa: BLE001 - e.g. the role may not create extensions
            log.warning("pgvector not available: %s", type(e).__name__)
            return False
    store._exec("CREATE TABLE IF NOT EXISTS help_chunks (id TEXT NOT NULL, lang TEXT NOT NULL, header TEXT NOT NULL, "
                "body TEXT NOT NULL, embedding TEXT NOT NULL, model TEXT NOT NULL, content_hash TEXT NOT NULL, "
                "updated_at TEXT NOT NULL, PRIMARY KEY (id, lang))")
    return True


def _vec_literal(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.7f}" for x in v) + "]"


def stored_hashes(store) -> dict[tuple[str, str], str]:
    return {(r["id"], r["lang"]): r["content_hash"] for r in store._all("SELECT id, lang, content_hash FROM help_chunks")}


def build_index(store, client=None) -> dict:
    """Embeds new or changed chunks (content_hash), removes chunks no longer in the guide."""
    from .store import now

    if not ensure_table(store):
        return {"embedded": 0, "kept": 0, "removed": 0, "available": False}
    current = chunks()
    have = stored_hashes(store)
    todo = [c for c in current if have.get((c.id, c.lang)) != c.content_hash()]
    vectors = embeddings.embed([c.text for c in todo], "passage", client) if todo else []
    ts, statements = now(), []
    for c, v in zip(todo, vectors):
        emb = _vec_literal(v) if store.pg else json.dumps([round(x, 7) for x in v])
        cast = "?::vector" if store.pg else "?"
        statements.append((
            f"INSERT INTO help_chunks (id, lang, header, body, embedding, model, content_hash, updated_at) "
            f"VALUES (?,?,?,?,{cast},?,?,?) ON CONFLICT (id, lang) DO UPDATE SET header = excluded.header, "
            "body = excluded.body, embedding = excluded.embedding, model = excluded.model, "
            "content_hash = excluded.content_hash, updated_at = excluded.updated_at",
            (c.id, c.lang, c.header, c.body, emb, embeddings.MODEL, c.content_hash(), ts)))
    keep = {(c.id, c.lang) for c in current}
    gone = [k for k in have if k not in keep]
    statements += [("DELETE FROM help_chunks WHERE id = ? AND lang = ?", k) for k in gone]
    if statements:
        store._many(statements)
    return {"embedded": len(todo), "kept": len(current) - len(todo), "removed": len(gone), "available": True}


def count(store) -> int:
    try:
        return int(store._all("SELECT COUNT(*) AS n FROM help_chunks")[0]["n"])
    except Exception:  # noqa: BLE001 - no table yet
        return 0


def attach(store) -> None:
    """Called once when the API opens its store. Optionally builds an empty index in the background."""
    global _store
    _store = store
    if os.getenv("HELP_INDEX_ON_START", "").lower() in ("1", "true", "yes") and embeddings.configured() \
            and count(store) == 0:
        def go() -> None:
            try:
                with _lock:
                    log.info("help index built: %s", build_index(store))
            except Exception as e:  # noqa: BLE001
                log.warning("help index not built: %s", type(e).__name__)
        threading.Thread(target=go, daemon=True).start()


def search(text: str, k: int = 10, store=None, client=None) -> list[tuple[str, float]]:
    """[(entry id, cosine)] best first, one row per entry (best language). [] when unavailable."""
    store = store or _store
    if store is None or not embeddings.configured() or not text.strip() or count(store) == 0:
        return []
    try:
        q = embeddings.embed([text], "query", client)[0]
    except embeddings.EmbeddingsUnavailable:
        return []
    if store.pg:
        rows = store._all("SELECT id, 1 - (embedding <=> ?::vector) AS cos FROM help_chunks "
                          "ORDER BY embedding <=> ?::vector LIMIT ?", (_vec_literal(q), _vec_literal(q), k * 2))
        scored = [(r["id"], float(r["cos"])) for r in rows]
    else:
        scored = [(r["id"], embeddings.cosine(q, json.loads(r["embedding"])))
                  for r in store._all("SELECT id, embedding FROM help_chunks")]
    best: dict[str, float] = {}
    for id_, cos in scored:
        best[id_] = max(cos, best.get(id_, -1.0))
    return sorted(best.items(), key=lambda kv: kv[1], reverse=True)[:k]
