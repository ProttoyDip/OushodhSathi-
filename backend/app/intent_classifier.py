"""Sathi intent classifier: ESCALATE-ONLY, switched off by default.

Catches medical questions that slip past guard.py's word lists (Banglish, typos). Contract:
- It runs AFTER guard.py, on a question the guard did not already route to a human.
- It can only move a question TOWARDS "medical" or "emergency"; it can never move one to "app".
- If it is off, missing, slow or failing, behaviour is exactly as without it.

Model: multilingual sentence embeddings from NVIDIA's API (app/embeddings.py:
nvidia/nemotron-3.5-embed-1b, Bengali among its listed languages, kept at 1024 dimensions; the
earlier baai/bge-m3 reached end of life on NVIDIA on 2026-08-25) + a scikit-learn logistic regression
trained offline by
eval/train_intent_model.py and saved as small JSON (coefficients only), so the server needs no
scikit-learn. Enable with SATHI_INTENT_MODEL=on, only after eval/run_intent_eval.py passes on at
least 200 human-written held-out examples.
"""
from __future__ import annotations

import json
import logging
import math
import os
from functools import lru_cache
from pathlib import Path

import httpx

from . import embeddings

log = logging.getLogger("oushodh.intent")

MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "intent_model.json"
EMBED_MODEL = embeddings.MODEL
TIMEOUT_S = 3.0
ESCALATE_AT = 0.5        # probability needed to move a question towards a human
RANK = {"APP": 0, "OTHER": 0, "MEDICAL": 1, "EMERGENCY": 2}


def _env(name: str) -> str:
    return os.getenv(name, "").split("#", 1)[0].strip()


def enabled() -> bool:
    return _env("SATHI_INTENT_MODEL").lower() == "on" and MODEL_PATH.exists() and embeddings.configured()


@lru_cache(maxsize=1)
def _model() -> dict:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def embed(texts: list[str], client: httpx.Client | None = None) -> list[list[float]]:
    """Question embeddings (input_type "query"). Raises on any error; callers fall back."""
    return embeddings.embed(texts, "query", client or httpx.Client(timeout=TIMEOUT_S))


def predict(vector: list[float], model: dict) -> dict[str, float]:
    """Softmax over the saved logistic-regression weights: {"APP": p, "MEDICAL": p, "EMERGENCY": p}."""
    scores = [sum(w * x for w, x in zip(coef, vector)) + b for coef, b in zip(model["coef"], model["intercept"])]
    if len(scores) == 1:  # binary model saved by scikit-learn: one row for the positive class
        p = 1 / (1 + math.exp(-scores[0]))
        return {model["classes"][0]: 1 - p, model["classes"][1]: p}
    top = max(scores)
    exps = [math.exp(s - top) for s in scores]
    total = sum(exps)
    return {c: e / total for c, e in zip(model["classes"], exps)}


def escalate(question: str, intent: str, client: httpx.Client | None = None) -> str:
    """Returns `intent` or a MORE cautious one (MEDICAL / EMERGENCY). Never less cautious."""
    if intent not in ("APP", "OTHER", "MEDICAL") or not enabled():
        return intent
    try:
        probs = predict(embed([question], client)[0], _model())
    except Exception as e:  # noqa: BLE001 - any failure means "behave as if the model did not exist"
        log.info("intent model skipped: %s", type(e).__name__)
        return intent
    best, p = max(((k.upper(), v) for k, v in probs.items()), key=lambda kv: kv[1])
    if p >= ESCALATE_AT and RANK.get(best, 0) > RANK.get(intent, 0):
        return best
    return intent
