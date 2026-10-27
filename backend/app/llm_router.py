"""The one place that talks to language models. Every provider is OpenAI-compatible.

Order per task: NVIDIA -> OpenRouter -> NARAROUTER -> EXPLAB -> AGENTROUTER -> Ollama (local).
Bangla explanations go to Ollama first (private, local) with cloud as fallback.
Responses are cached in SQLite by SHA-256 of (task, model, messages).
Never logs API keys or photo bytes.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Literal

import httpx

log = logging.getLogger("oushodh.router")

Task = Literal["vision", "text", "explain_bn", "sathi"]
# Bangla writing for families: local Ollama first (private), and the global model choice does not apply
LOCAL_FIRST = ("explain_bn", "sathi")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
NVIDIA_BASE = "https://integrate.api.nvidia.com/v1"  # NVIDIA API catalog (build.nvidia.com)
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


_auto_models: dict[str, list[str]] = {}
OPENROUTER_FALLBACK = "openrouter/free"  # OpenRouter's own router across whatever is free today
AUTO_LIMIT = 3

# The user's chosen model per task ("vision" | "text"), as (provider, model). Loaded from the
# store by the API at startup and whenever it changes; moves that model to the front.
_preferred: dict[str, tuple[str, str]] = {}
# What actually answered last, per task: shown in the app so the model in use is visible.
last_used: dict[str, dict] = {}


def set_preferred(kind: str, provider: str | None, model: str | None) -> None:
    if provider and model:
        _preferred[kind] = (provider, model)
    else:
        _preferred.pop(kind, None)


def preferred(kind: str) -> tuple[str, str] | None:
    return _preferred.get(kind)


def _probe(model: str, key: str, client: httpx.Client) -> bool:
    """One-token call: free models come and go (some are agent-app only), so test before trusting."""
    try:
        r = client.post(f"{OPENROUTER_BASE}/chat/completions", headers={"Authorization": f"Bearer {key}"},
                        json={"model": model, "max_tokens": 1, "messages": [{"role": "user", "content": "hi"}]})
        return r.status_code == 200
    except httpx.HTTPError:
        return False


def free_openrouter_candidates(kind: Literal["vision", "text"], client: httpx.Client | None = None) -> list[str]:
    """Free OpenRouter chat models (price 0) with the right input, largest context first. Not probed."""
    try:
        c = client or httpx.Client(timeout=20)
        data = c.get(f"{OPENROUTER_BASE}/models").json().get("data", [])
    except (httpx.HTTPError, ValueError) as e:
        log.warning("OpenRouter model list failed: %s", type(e).__name__)
        return []

    def free(m: dict) -> bool:
        p = m.get("pricing") or {}
        try:
            return float(p.get("prompt", 1)) == 0 and float(p.get("completion", 1)) == 0
        except (TypeError, ValueError):
            return False

    want = "image" if kind == "vision" else "text"
    arch = lambda m: m.get("architecture") or {}  # noqa: E731
    candidates = [
        m for m in data
        if free(m) and want in (arch(m).get("input_modalities") or [])
        and (arch(m).get("output_modalities") or ["text"]) == ["text"]
    ]
    return [m["id"] for m in sorted(candidates, key=lambda m: -(m.get("context_length") or 0))]


def pick_free_openrouter_models(kind: Literal["vision", "text"], key: str = "",
                                client: httpx.Client | None = None) -> list[str]:
    """Up to AUTO_LIMIT free models that actually answer, then openrouter/free as the last resort.
    Probed once per process and cached."""
    if kind in _auto_models:
        return _auto_models[kind]
    c = client or httpx.Client(timeout=20)
    working: list[str] = []
    for model in free_openrouter_candidates(kind, c):
        if model == OPENROUTER_FALLBACK:
            continue
        if not key or _probe(model, key, c):
            working.append(model)
        if len(working) >= AUTO_LIMIT:
            break
    picked = working + [OPENROUTER_FALLBACK]
    _auto_models[kind] = picked
    log.info("free OpenRouter %s models (probed): %s", kind, ", ".join(picked))
    return picked


def pick_free_openrouter_model(kind: Literal["vision", "text"], client: httpx.Client | None = None) -> str | None:
    """Back-compat: the first auto-picked model."""
    models = pick_free_openrouter_models(kind, "", client)
    return models[0] if models else None


def router_model(prefix: str, task: Task) -> str:
    """Model a fallback router uses for a task. For photos, <PREFIX>_VISION_MODEL wins when
    set; "none" keeps a text-only router out of the photo-reading chain."""
    if task == "vision":
        vision = _env(f"{prefix}_VISION_MODEL")
        if vision.lower() in ("none", "-", "off"):
            return ""
        if vision:
            return vision
    return _env(f"{prefix}_MODEL")


def configured_providers(task: Task, client: httpx.Client | None = None) -> list[Provider]:
    kind = "vision" if task == "vision" else "text"
    out: list[Provider] = []
    # NVIDIA's own API leads: in testing it read cut strips correctly where the free
    # OpenRouter copies did not, and wrote clean Bangla. NVIDIA_VISION_MODEL for photos.
    if (key := _env("NVIDIA_API_KEY")) and (model := router_model("NVIDIA", task)):
        out.append(Provider("nvidia", (_env("NVIDIA_BASE_URL") or NVIDIA_BASE).rstrip("/"), key, model))
    if key := _env("OPENROUTER_API_KEY"):
        env_model = _env("OPENROUTER_VISION_MODEL" if kind == "vision" else "OPENROUTER_TEXT_MODEL")
        models = ([env_model] if env_model else []) + pick_free_openrouter_models(kind, key, client)
        for m in dict.fromkeys(models):  # keep order, drop repeats
            out.append(Provider("openrouter", OPENROUTER_BASE, key, m))
    for prefix in ("NARAROUTER", "EXPLAB", "AGENTROUTER"):
        base, key, model = _env(f"{prefix}_BASE_URL"), _env(f"{prefix}_API_KEY"), router_model(prefix, task)
        if base and key and model:
            out.append(Provider(prefix.lower(), base.rstrip("/"), key, model))
    ollama_model = _env("OLLAMA_VISION_MODEL") if task == "vision" else _env("OLLAMA_MODEL")
    if (base := _env("OLLAMA_BASE_URL")) and ollama_model and _env("OLLAMA_DISABLED").lower() not in ("1", "true"):
        ollama = Provider("ollama", base.rstrip("/"), "ollama", ollama_model)
        if task in LOCAL_FIRST:
            out.insert(0, ollama)  # private and local first for Bangla explanations
        else:
            out.append(ollama)
    # the user's chosen model goes first; the rest of the chain stays as the fallback
    if (pref := _preferred.get(kind)) and task not in LOCAL_FIRST:
        chosen = [p for p in out if (p.name, p.model) == pref]
        out = chosen + [p for p in out if (p.name, p.model) != pref]
    return out


def provider_names(task: Task) -> list[str]:
    """For /health: names only, never keys. Does not trigger model auto-pick."""
    names = []
    if _env("NVIDIA_API_KEY") and router_model("NVIDIA", task):
        names.append("nvidia")
    if _env("OPENROUTER_API_KEY"):
        names.append("openrouter")
    names += [p.lower() for p in ("NARAROUTER", "EXPLAB", "AGENTROUTER")
              if _env(f"{p}_BASE_URL") and _env(f"{p}_API_KEY") and router_model(p, task)]
    if _env("OLLAMA_BASE_URL") and (_env("OLLAMA_VISION_MODEL") if task == "vision" else _env("OLLAMA_MODEL")):
        names.insert(0 if task in LOCAL_FIRST else len(names), "ollama")
    return names


def cache_key(task: str, model: str, messages: list[dict]) -> str:
    raw = json.dumps([task, model, messages], sort_keys=True, ensure_ascii=False)
    return "llm:" + hashlib.sha256(raw.encode()).hexdigest()


class Router:
    def __init__(self, store=None, client: httpx.Client | None = None, timeout: float = 60):
        self.store = store
        self.client = client or httpx.Client(timeout=timeout)

    def chat(self, task: Task, messages: list[dict], *, json_mode: bool = False,
             temperature: float = 0, budget_s: float | None = None) -> RouterResult:
        """budget_s: total seconds for the whole chain. For callers with a safe fixed fallback
        (Sathi), a slow model is worse than no model: stop trying once the budget is spent."""
        started = time.monotonic()
        providers = configured_providers(task, self.client)
        if not providers:
            raise NoProviderAvailable(f"no provider configured for task {task!r}")
        errors = []
        for p in providers:
            key = cache_key(task, p.model, messages)
            if self.store is not None and (hit := self.store.cache_get(key)) is not None:
                log.info("task=%s cache hit (%s/%s)", task, p.name, p.model)
                last_used[task] = {"provider": p.name, "model": p.model, "at": time.time(), "cached": True}
                return RouterResult(hit, p.name, p.model, cached=True)
            timeout = None
            if budget_s is not None:
                timeout = budget_s - (time.monotonic() - started)
                if timeout < 1:
                    errors.append(f"{p.name}: over the {budget_s:g}s budget")
                    break
            body: dict = {"model": p.model, "messages": messages, "temperature": temperature}
            if json_mode and p.name != "ollama":
                body["response_format"] = {"type": "json_object"}
            try:
                r = self.client.post(
                    f"{p.base_url}/chat/completions", json=body,
                    headers={"Authorization": f"Bearer {p.api_key}"},
                    **({"timeout": timeout} if timeout is not None else {}),
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
            last_used[task] = {"provider": p.name, "model": p.model, "at": time.time()}
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
