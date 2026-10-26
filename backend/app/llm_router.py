"""The one place that talks to language models. Every provider is OpenAI-compatible.

Order per task: OpenRouter -> NARAROUTER -> EXPLAB -> AGENTROUTER -> Ollama (local).
Bangla explanations go to Ollama first (private, local) with cloud as fallback.
Responses are cached in SQLite by SHA-256 of (task, model, messages).
Never logs API keys or photo bytes.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from typing import Literal

import httpx

log = logging.getLogger("oushodh.router")

Task = Literal["vision", "text", "explain_bn"]
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
FALLTHROUGH_STATUS = {408, 409, 425, 429} | set(range(500, 600))


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    api_key: str
    model: str


@dataclass(frozen=True)
class RouterResult:
    text: str
    provider: str
    model: str
    cached: bool = False


class NoProviderAvailable(RuntimeError):
    pass


def _env(name: str) -> str:
    # tolerate inline comments copied from .env.example ("KEY=   # note")
    return os.getenv(name, "").split("#", 1)[0].strip()


_auto_models: dict[str, str] = {}


def pick_free_openrouter_model(kind: Literal["vision", "text"], client: httpx.Client | None = None) -> str | None:
    """Call OpenRouter's model list once and pick a free model (prompt and completion
    price 0) with the right input modality, preferring the largest context window."""
    if kind in _auto_models:
        return _auto_models[kind]
    try:
        c = client or httpx.Client(timeout=20)
        data = c.get(f"{OPENROUTER_BASE}/models").json().get("data", [])
    except (httpx.HTTPError, ValueError) as e:
        log.warning("OpenRouter model list failed: %s", type(e).__name__)
        return None

    def free(m: dict) -> bool:
        p = m.get("pricing") or {}
        try:
            return float(p.get("prompt", 1)) == 0 and float(p.get("completion", 1)) == 0
        except (TypeError, ValueError):
            return False

    want = "image" if kind == "vision" else "text"
    candidates = [
        m for m in data
        if free(m) and want in ((m.get("architecture") or {}).get("input_modalities") or [])
        and "text" in ((m.get("architecture") or {}).get("output_modalities") or ["text"])
    ]
    if not candidates:
        return None
    best = max(candidates, key=lambda m: m.get("context_length") or 0)["id"]
    _auto_models[kind] = best
    log.info("auto-picked free OpenRouter %s model: %s", kind, best)
    return best


def configured_providers(task: Task, client: httpx.Client | None = None) -> list[Provider]:
    out: list[Provider] = []
    if key := _env("OPENROUTER_API_KEY"):
        env_model = _env("OPENROUTER_VISION_MODEL" if task == "vision" else "OPENROUTER_TEXT_MODEL")
        model = env_model or pick_free_openrouter_model("vision" if task == "vision" else "text", client)
        if model:
            out.append(Provider("openrouter", OPENROUTER_BASE, key, model))
    for prefix in ("NARAROUTER", "EXPLAB", "AGENTROUTER"):
        base, key, model = _env(f"{prefix}_BASE_URL"), _env(f"{prefix}_API_KEY"), _env(f"{prefix}_MODEL")
        if base and key and model:
            out.append(Provider(prefix.lower(), base.rstrip("/"), key, model))
    ollama_model = _env("OLLAMA_VISION_MODEL") if task == "vision" else _env("OLLAMA_MODEL")
    if (base := _env("OLLAMA_BASE_URL")) and ollama_model and _env("OLLAMA_DISABLED").lower() not in ("1", "true"):
        ollama = Provider("ollama", base.rstrip("/"), "ollama", ollama_model)
        if task == "explain_bn":
            out.insert(0, ollama)  # private and local first for Bangla explanations
        else:
            out.append(ollama)
    return out


def provider_names(task: Task) -> list[str]:
    """For /health: names only, never keys. Does not trigger model auto-pick."""
    names = []
    if _env("OPENROUTER_API_KEY"):
        names.append("openrouter")
    names += [p.lower() for p in ("NARAROUTER", "EXPLAB", "AGENTROUTER")
              if _env(f"{p}_BASE_URL") and _env(f"{p}_API_KEY") and _env(f"{p}_MODEL")]
    if _env("OLLAMA_BASE_URL") and (_env("OLLAMA_VISION_MODEL") if task == "vision" else _env("OLLAMA_MODEL")):
        names.insert(0 if task == "explain_bn" else len(names), "ollama")
    return names


def cache_key(task: str, model: str, messages: list[dict]) -> str:
    raw = json.dumps([task, model, messages], sort_keys=True, ensure_ascii=False)
    return "llm:" + hashlib.sha256(raw.encode()).hexdigest()


class Router:
    def __init__(self, store=None, client: httpx.Client | None = None, timeout: float = 60):
        self.store = store
        self.client = client or httpx.Client(timeout=timeout)

    def chat(self, task: Task, messages: list[dict], *, json_mode: bool = False,
             temperature: float = 0) -> RouterResult:
        providers = configured_providers(task, self.client)
        if not providers:
            raise NoProviderAvailable(f"no provider configured for task {task!r}")
        errors = []
        for p in providers:
            key = cache_key(task, p.model, messages)
            if self.store is not None and (hit := self.store.cache_get(key)) is not None:
                log.info("task=%s cache hit (%s/%s)", task, p.name, p.model)
                return RouterResult(hit, p.name, p.model, cached=True)
            body: dict = {"model": p.model, "messages": messages, "temperature": temperature}
            if json_mode and p.name != "ollama":
                body["response_format"] = {"type": "json_object"}
            try:
                r = self.client.post(
                    f"{p.base_url}/chat/completions", json=body,
                    headers={"Authorization": f"Bearer {p.api_key}"},
                )
            except httpx.HTTPError as e:  # timeouts, connection refused (e.g. Ollama not running)
                log.warning("task=%s provider=%s failed: %s; falling through", task, p.name, type(e).__name__)
                errors.append(f"{p.name}: {type(e).__name__}")
                continue
            if r.status_code >= 400:
                # 429/5xx are expected fall-throughs; other 4xx (e.g. model lacks vision) also fall through
                level = logging.WARNING if r.status_code in FALLTHROUGH_STATUS else logging.ERROR
                log.log(level, "task=%s provider=%s HTTP %s; falling through", task, p.name, r.status_code)
                errors.append(f"{p.name}: HTTP {r.status_code}")
                continue
            try:
                text = r.json()["choices"][0]["message"]["content"] or ""
            except (ValueError, KeyError, IndexError, TypeError):
                errors.append(f"{p.name}: malformed response")
                continue
            log.info("task=%s answered by provider=%s model=%s", task, p.name, p.model)
            if self.store is not None:
                self.store.cache_set(key, text)
            return RouterResult(text, p.name, p.model)
        raise NoProviderAvailable("all providers failed: " + "; ".join(errors))


def parse_json(text: str) -> dict:
    """Models sometimes wrap JSON in ``` fences or prose; take the outermost object."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in model output")
    return json.loads(text[start:end + 1])
