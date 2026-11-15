"""Sathi's contextual hybrid retrieval (keyword + vector, RRF). The embedding API is mocked."""
import hashlib
import math

import pytest

from app import embeddings, help_index, help_vectors, sathi


def fake_vector(text: str) -> list[float]:
    """A deterministic bag-of-words vector: texts sharing words get a high cosine."""
    v = [0.0] * embeddings.DIM
    for w in help_index.normalise(text).split():
        v[int(hashlib.md5(w.encode()).hexdigest(), 16) % embeddings.DIM] += 1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


@pytest.fixture
def mocked(monkeypatch):
    calls = []

    def embed(texts, kind, client=None):
        calls.append((kind, list(texts)))
        return [fake_vector(t) for t in texts]

    monkeypatch.setenv("NVIDIA_API_KEY", "nv-key")
    monkeypatch.setattr(embeddings, "embed", embed)
    return calls


@pytest.fixture
def indexed(store, mocked):
    help_vectors.build_index(store)
    help_vectors.attach(store)
    yield store
    help_vectors._store = None


def test_headers_are_deterministic_and_carry_both_languages():
    e = help_index.entries()["scan.cut-strip"]
    h_bn, h_en = help_vectors.header_for(e, "bn"), help_vectors.header_for(e, "en")
    assert h_bn == help_vectors.header_for(e, "bn")
    for h in (h_bn, h_en):
        assert e.question["bn"] in h and e.question["en"] in h and e.group["en"] in h
    assert "ছবি তোলার পাতা" in h_bn and "scan screen" in h_en
    chunks = help_vectors.chunks()
    assert len(chunks) == 2 * len(help_index.entries())
    assert {c.lang for c in chunks} == {"bn", "en"}


def test_reindex_embeds_only_changed_chunks(store, mocked, monkeypatch):
    first = help_vectors.build_index(store)
    assert first["embedded"] == len(help_vectors.chunks()) and first["available"]
    assert help_vectors.build_index(store)["embedded"] == 0          # nothing changed
    original = help_vectors.chunks()
    changed = [help_vectors.Chunk(c.id, c.lang, c.header, c.body + " (edited)") if c.id == "scan.blurry" else c
               for c in original]
    monkeypatch.setattr(help_vectors, "chunks", lambda: changed)
    assert help_vectors.build_index(store)["embedded"] == 2         # the edited entry, both languages
    monkeypatch.setattr(help_vectors, "chunks", lambda: [c for c in changed if c.id != "scan.blurry"])
    assert help_vectors.build_index(store)["removed"] == 2
    assert all(kind == "passage" for kind, _ in mocked)


def test_rrf_orders_by_reciprocal_rank_and_keeps_thresholds():
    ents = list(help_index.entries().values())[:3]
    keyword = [help_index.Hit(ents[0], 70.0), help_index.Hit(ents[1], 50.0), help_index.Hit(ents[2], 40.0)]
    vector = [(ents[1].id, 0.9), (ents[2].id, 0.2), (ents[0].id, 0.1)]
    fused = help_index.fuse(keyword, vector, k=3)
    # entry 1: 1/62 + 1/61 beats entry 0: 1/61 + 1/63
    assert [h.entry.id for h in fused] == [ents[1].id, ents[0].id, ents[2].id]
    assert fused[0].score == help_index.MATCH_THRESHOLD   # rescued by a strong vector match, never STRONG
    assert fused[2].score == 40.0                          # weak vector match: keyword score unchanged
    assert not any(h.agreed for h in fused)                # rank 1 differs between the two
    agreed = help_index.fuse(keyword, [(ents[0].id, 0.2)], k=1)
    assert agreed[0].agreed


def test_without_a_key_search_is_exactly_keyword_search(store, monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "")
    help_vectors.attach(store)
    try:
        q = "পাসপোর্ট প্রিন্ট করব কীভাবে"
        assert help_index.search(q) == help_index.keyword_search(q)[:3]
    finally:
        help_vectors._store = None


def test_sqlite_path_finds_the_right_entry(indexed):
    hits = help_vectors.search("how do I print the medicine passport", store=indexed)
    assert hits[0][0] == "passport.print"


def test_query_embeddings_use_query_type_and_redacted_text(indexed, mocked):
    mocked.clear()
    sathi.classify_question("Rahima er passport print korbo kivabe", None, redact=["Rahima"])
    queries = [texts for kind, texts in mocked if kind == "query"]
    assert queries and all("Rahima" not in t for batch in queries for t in batch)


def test_guard_runs_before_retrieval(indexed, mocked):
    mocked.clear()
    assert sathi.classify_question("বাবার বুকে ব্যথা হচ্ছে", None)[0] == "EMERGENCY"
    assert sathi.classify_question("Can I stop taking amlodipine?", None)[0] == "MEDICAL"
    assert mocked == []  # no embedding call at all for medical or emergency questions


def test_below_threshold_is_not_in_the_guide(indexed):
    reply = sathi.ask("xqzv plorb wexx", "en", 1, None)
    assert reply.kind in ("not_in_guide", "medical_redirect")


def test_embedding_failure_falls_back(store, monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nv-key")

    def broken(texts, kind, client=None):
        raise embeddings.EmbeddingsUnavailable("down")

    monkeypatch.setattr(embeddings, "embed", broken)
    store._exec("CREATE TABLE IF NOT EXISTS help_chunks (id TEXT, lang TEXT, header TEXT, body TEXT, embedding TEXT, "
                "model TEXT, content_hash TEXT, updated_at TEXT, PRIMARY KEY (id, lang))")
    store._exec("INSERT INTO help_chunks VALUES ('x','en','h','b','[0.0]','m','h','t')")
    help_vectors.attach(store)
    try:
        q = "how do I print the passport"
        assert help_index.search(q) == help_index.keyword_search(q)[:3]
    finally:
        help_vectors._store = None


def test_embeddings_module_normalises_and_truncates():
    v = embeddings.normalise([3.0, 4.0] + [0.0] * 3000)
    assert len(v) == embeddings.DIM and abs(sum(x * x for x in v) - 1) < 1e-9
    assert embeddings.cache_key("a", "query") != embeddings.cache_key("a", "passage")
