"""Escalate-only intent classifier: the safety contract, with a fake model and fake embeddings."""
import json

import httpx
import pytest

from app import intent_classifier as ic
from app import sathi


@pytest.fixture
def fake_model(tmp_path, monkeypatch):
    """A 2-dimensional 'model': dimension 0 votes APP, dimension 1 votes MEDICAL."""
    path = tmp_path / "intent_model.json"
    path.write_text(json.dumps({"classes": ["APP", "EMERGENCY", "MEDICAL"],
                                "coef": [[4.0, 0.0], [0.0, 0.0], [0.0, 4.0]], "intercept": [0.0, -5.0, 0.0]}))
    monkeypatch.setattr(ic, "MODEL_PATH", path)
    ic._model.cache_clear()
    monkeypatch.setenv("SATHI_INTENT_MODEL", "on")
    monkeypatch.setenv("NVIDIA_API_KEY", "nv-key")
    yield path
    ic._model.cache_clear()


def client_returning(vector, status=200):
    def handler(request):
        assert json.loads(request.content)["model"] == ic.EMBED_MODEL
        return httpx.Response(status, json={"data": [{"index": 0, "embedding": vector}]})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_off_by_default(monkeypatch):
    monkeypatch.delenv("SATHI_INTENT_MODEL", raising=False)
    assert ic.enabled() is False
    assert ic.escalate("anything", "APP") == "APP"


def test_can_move_app_towards_medical(fake_model):
    assert ic.escalate("ma ke 2ta napa", "APP", client_returning([0.0, 1.0])) == "MEDICAL"
    assert ic.escalate("ma ke 2ta napa", "OTHER", client_returning([0.0, 1.0])) == "MEDICAL"


def test_never_moves_medical_or_emergency_towards_app(fake_model):
    assert ic.escalate("question", "MEDICAL", client_returning([1.0, 0.0])) == "MEDICAL"
    assert ic.escalate("question", "EMERGENCY", client_returning([1.0, 0.0])) == "EMERGENCY"
    assert ic.escalate("question", "INJECTION", client_returning([1.0, 0.0])) == "INJECTION"


def test_failures_change_nothing(fake_model):
    assert ic.escalate("question", "APP", client_returning([0.0, 1.0], status=500)) == "APP"
    assert ic.escalate("question", "APP", client_returning([0.0])) == "APP"  # a malformed vector never escalates on a tie
    bad = httpx.Client(transport=httpx.MockTransport(lambda r: (_ for _ in ()).throw(httpx.ConnectTimeout("t"))))
    assert ic.escalate("question", "APP", bad) == "APP"


def test_missing_model_file_means_off(tmp_path, monkeypatch):
    monkeypatch.setattr(ic, "MODEL_PATH", tmp_path / "missing.json")
    monkeypatch.setenv("SATHI_INTENT_MODEL", "on")
    monkeypatch.setenv("NVIDIA_API_KEY", "nv-key")
    assert ic.enabled() is False


def test_softmax_probabilities_sum_to_one():
    probs = ic.predict([1.0, 2.0], {"classes": ["APP", "MEDICAL", "EMERGENCY"],
                                    "coef": [[1, 0], [0, 1], [0, 0]], "intercept": [0, 0, 0]})
    assert sum(probs.values()) == pytest.approx(1.0) and max(probs, key=probs.get) == "MEDICAL"


def test_guard_decisions_are_never_softened(fake_model, monkeypatch):
    """Even a model that always says APP cannot touch what guard.py routed to a human."""
    monkeypatch.setattr(ic, "embed", lambda texts, client=None: [[10.0, 0.0]])
    intent, _ = sathi.classify_question("বাবার বুকে ব্যথা হচ্ছে", None)
    assert intent == "EMERGENCY"
    intent, _ = sathi.classify_question("Can I stop taking amlodipine?", None)
    assert intent == "MEDICAL"


def test_shipped_dataset_heldout_is_human_and_labels_are_valid():
    import csv
    from pathlib import Path

    rows = list(csv.DictReader(open(Path(__file__).resolve().parents[2] / "eval" / "intent_dataset.csv", encoding="utf-8")))
    assert rows and {r["label"] for r in rows} <= {"app", "medical", "emergency"}
    assert all(r["source"] != "synthetic" for r in rows if r["split"] == "heldout")
