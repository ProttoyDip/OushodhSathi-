"""Train the escalate-only Sathi intent classifier (offline; never on the server).

  pip install -r eval/requirements-ml.txt
  NVIDIA_API_KEY=... python eval/train_intent_model.py

Embeds every TRAIN row of eval/intent_dataset.csv with NVIDIA's nvidia/nemotron-3.5-embed-1b via app/embeddings.py (cached in
eval/.intent_embed_cache.json so re-runs cost nothing), fits a scikit-learn logistic regression,
and writes backend/data/intent_model.json: coefficients and intercepts only, so the API runs it
without scikit-learn. Held-out rows are never used for training. Evaluate with run_intent_eval.py.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "backend" / ".env")

from app import intent_classifier  # noqa: E402

DATASET = ROOT / "eval" / "intent_dataset.csv"
CACHE = ROOT / "eval" / ".intent_embed_cache.json"
MIN_TRAIN = 60


def load_rows(split: str) -> list[dict]:
    with DATASET.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["split"] == split]


def embeddings(texts: list[str]) -> list[list[float]]:
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    key = lambda t: hashlib.sha256(f"{intent_classifier.EMBED_MODEL}|{t}".encode()).hexdigest()  # noqa: E731
    missing = [t for t in texts if key(t) not in cache]
    for i in range(0, len(missing), 32):
        batch = missing[i:i + 32]
        for t, v in zip(batch, intent_classifier.embed(batch)):
            cache[key(t)] = v
    CACHE.write_text(json.dumps(cache), encoding="utf-8")
    return [cache[key(t)] for t in texts]


def main() -> None:
    try:
        from sklearn.linear_model import LogisticRegression
    except ImportError:
        sys.exit("pip install -r eval/requirements-ml.txt (scikit-learn) first")
    train = load_rows("train")
    if len(train) < MIN_TRAIN or len({r["label"] for r in train}) < 2:
        sys.exit(f"Not enough training data yet: {len(train)} train rows (need {MIN_TRAIN}+ across labels). "
                 "Add examples with eval/add_intent_example.py.")
    X = embeddings([r["text"] for r in train])
    y = [r["label"].upper() for r in train]
    clf = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X, y)
    out = {
        "classes": list(clf.classes_), "coef": clf.coef_.tolist(), "intercept": clf.intercept_.tolist(),
        "embed_model": intent_classifier.EMBED_MODEL, "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "train_rows": len(train), "synthetic_rows": sum(r["source"] == "synthetic" for r in train),
    }
    intent_classifier.MODEL_PATH.write_text(json.dumps(out), encoding="utf-8")
    print(f"wrote {intent_classifier.MODEL_PATH} ({len(train)} train rows). Now run eval/run_intent_eval.py.")


if __name__ == "__main__":
    main()
