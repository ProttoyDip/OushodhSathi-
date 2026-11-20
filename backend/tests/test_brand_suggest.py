"""'Did you mean?' for unrecognised brands: spelling, plus embeddings across scripts (mocked)."""
from app import brand_suggest, embeddings
from app.models import MedicineItemIn
from tests.test_clinical import household
from tests.test_hybrid_retrieval import fake_vector


def names(q):
    return [s["brand"] for s in brand_suggest.suggest(q)]


def test_typos_and_cut_off_names_get_the_right_brand_first():
    assert names("Camlodn")[0] == "Camlodin"
    assert names("Seclo2")[0] == "Seclo"
    assert names("Aec")[0] == "Ace"
    assert names("Napa Extr")[:2] == ["Napa Extra", "Napa"]


def test_bangla_aliases_and_nothing_close():
    assert names("নাপা")[0] == "Napa"
    assert names("xyzqq") == [] and names("") == []
    assert len(brand_suggest.suggest("Napa")) <= 3


def test_embeddings_add_meaning_and_failures_fall_back(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nv")
    brand_suggest._brand_vectors.clear()
    kinds = []

    def embed(texts, kind, client=None):
        kinds.append(kind)
        return [fake_vector(t) for t in texts]

    monkeypatch.setattr(embeddings, "embed", embed)
    out = names("losartan")   # no brand is spelled like it; the generic in the brand passages matches
    assert set(out) & {"Osartil", "Angilock", "Osartil Plus"} and {"passage", "query"} <= set(kinds)

    def broken(texts, kind, client=None):
        raise embeddings.EmbeddingsUnavailable("down")

    monkeypatch.setattr(embeddings, "embed", broken)
    brand_suggest._brand_vectors.clear()
    assert names("Camlodn")[0] == "Camlodin"   # spelling alone still works


def test_suggest_endpoint(client):
    r = client.get("/brands/suggest", params={"q": "Camlodn"})
    assert r.status_code == 200 and r.json()[0] == {"brand": "Camlodin", "generic": "amlodipine", "strength": r.json()[0]["strength"]}
    assert client.get("/brands/suggest", params={"q": ""}).status_code == 422


def test_editing_the_reading_clears_the_second_read(client, store):
    pid = household(client)
    it = store.add_item(pid, MedicineItemIn(brand="Napa", strength="50 mg", confidence=0.9),
                        second_read={"strength": "disagree", "expiry": "unknown", "model": "m",
                                     "seen_strengths": ["500 mg"], "seen_expiries": []})
    r = client.patch(f"/items/{it.id}", json={"strength": "500 mg"}).json()
    assert r["second_read"] is None and r["needs_review"] is False


def test_unrelated_medicines_are_never_suggested():
    # A misread of "Rupadin" (rupatadine): before the fix, "Tryptin" (amitriptyline) came first.
    assert "Tryptin" not in names("Rupain")
    assert all(n[0].lower() == "r" for n in names("Rupain"))


def test_meaning_hits_must_also_look_plausible(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nv")
    brand_suggest._brand_vectors.clear()
    monkeypatch.setattr(embeddings, "embed", lambda texts, kind, client=None: [[1.0] + [0.0] * 3 for _ in texts])
    # every brand is "close in meaning" to everything here, yet only plausible names come back
    assert "Tryptin" not in names("Rupain")
    assert names("Camlodn")[0] == "Camlodin"
