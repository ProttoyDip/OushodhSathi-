"""Text embeddings from NVIDIA's API, shared by Sathi's hybrid retrieval and the intent classifier.

Model: nvidia/nemotron-3.5-embed-1b (https://build.nvidia.com/nvidia/nemotron-3_5-embed-1b), the
current NVIDIA multilingual text embedding model; its card lists Bengali among 34 text languages.
Checked against the live API on 2026-11-15:
- POST https://integrate.api.nvidia.com/v1/embeddings, OpenAI-compatible
- "input_type" is REQUIRED for this asymmetric model: "query" for questions, "passage" for documents
- native size 2048; the card says embeddings may be truncated from the end and must then be
  re-normalised. We keep 1024 dimensions: pgvector's HNSW index supports at most 2,000 dimensions for
  the vector type (https://github.com/pgvector/pgvector), and 1024 is plenty for a ~100-entry guide.
- truncate="END" cuts over-long input instead of failing.
(baai/bge-m3, used before, reached end of life on NVIDIA on 2026-08-25 and now returns HTTP 410.)

Every call: batches of BATCH, 10 s timeout, two retries on transient errors, and a cache keyed by
sha256(model + input_type + text) so the same text is never embedded twice in a process. Callers
treat any EmbeddingsUnavailable as "no vectors": behaviour then is exactly as without embeddings.
"""
from __future__ import annotations

import hashlib
import logging
import math
import os
import time
from typing import Literal

import httpx

log = logging.getLogger("oushodh.embeddings")

URL = "https://integrate.api.nvidia.com/v1/embeddings"
MODEL = "nvidia/nemotron-3.5-embed-1b"
DIM = 1024
BATCH = 32
TIMEOUT_S = 10.0
RETRIES = 2
RETRY_STATUS = {408, 425, 429} | set(range(500, 600))

Kind = Literal["query", "passage"]
_cache: dict[str, list[float]] = {}


class EmbeddingsUnavailable(RuntimeError):
    pass


def _env(name: str) -> str:
    return os.getenv(name, "").split("#", 1)[0].strip()


def configured() -> bool:
    return bool(_env("NVIDIA_API_KEY")) and _env("EMBEDDINGS_DISABLED").lower() not in ("1", "true", "yes")


def cache_key(text: str, kind: Kind, model: str = MODEL) -> str:
    return hashlib.sha256(f"{model}|{kind}|{text}".encode()).hexdigest()


def normalise(v: list[float], dim: int = DIM) -> list[float]:
    """Truncate to `dim` and re-normalise to unit length (as the model card requires)."""
    v = v[:dim]
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def cosine(a: list[float], b: list[float]) -> float:
    """Both vectors are unit length after normalise(), so the dot product is the cosine."""
    return sum(x * y for x, y in zip(a, b))


def _post(texts: list[str], kind: Kind, client: httpx.Client) -> list[list[float]]:
    body = {"model": MODEL, "input": texts, "input_type": kind, "encoding_format": "float", "truncate": "END"}
    last: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            r = client.post(URL, headers={"Authorization": f"Bearer {_env('NVIDIA_API_KEY')}"}, json=body)
            if r.status_code in RETRY_STATUS and attempt < RETRIES:
                time.sleep(0.5 * (attempt + 1))
                continue
            r.raise_for_status()
            data = sorted(r.json()["data"], key=lambda d: d["index"])
            return [normalise(d["embedding"]) for d in data]
        except (httpx.HTTPError, KeyError, ValueError) as e:
            last = e
            if attempt < RETRIES and not isinstance(e, httpx.HTTPStatusError):
                time.sleep(0.5 * (attempt + 1))
                continue
            break
    raise EmbeddingsUnavailable(type(last).__name__ if last else "unknown")


def embed(texts: list[str], kind: Kind, client: httpx.Client | None = None) -> list[list[float]]:
    """Unit vectors of length DIM, in input order. Raises EmbeddingsUnavailable."""
    if not configured():
        raise EmbeddingsUnavailable("not configured")
    missing = list(dict.fromkeys(t for t in texts if cache_key(t, kind) not in _cache))
    if missing:
        c = client or httpx.Client(timeout=TIMEOUT_S)
        for i in range(0, len(missing), BATCH):
            batch = missing[i:i + BATCH]
            for t, v in zip(batch, _post(batch, kind, c)):
                _cache[cache_key(t, kind)] = v
    return [_cache[cache_key(t, kind)] for t in texts]
