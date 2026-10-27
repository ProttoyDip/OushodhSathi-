import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Tests never call real providers: blank every key before the app reads the environment
_BLANK = ["NVIDIA_API_KEY", "OPENROUTER_API_KEY", "NARAROUTER_BASE_URL", "EXPLAB_BASE_URL", "AGENTROUTER_BASE_URL",
          "TAVILY_API_KEY", "PERPLEXITY_API_KEY", "N8N_ALERT_WEBHOOK"]


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch):
    for k in _BLANK:
        monkeypatch.setenv(k, "")
    monkeypatch.setenv("OLLAMA_DISABLED", "1")
    # no live free-model discovery in tests: the chain is exactly what each test configures
    from app import llm_router
    monkeypatch.setattr(llm_router, "_auto_models", {"vision": [], "text": []})
    monkeypatch.setattr(llm_router, "_preferred", {})
    monkeypatch.setenv("REVIEWER_TOKEN", "test-token")
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from app import ratelimit
    ratelimit.windows.reset()


@pytest.fixture
def store(tmp_path):
    from app.store import Store
    return Store(tmp_path / "test.db")


@pytest.fixture
def client(store):
    from fastapi.testclient import TestClient

    from app import main
    main.app.dependency_overrides[main.get_store] = lambda: store
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()
