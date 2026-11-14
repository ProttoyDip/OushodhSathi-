"""Train the missed-dose risk model (offline). REFUSES without enough real pilot data.

  pip install -r eval/requirements-ml.txt
  DATABASE_URL=... python eval/train_adherence_model.py      # reads the pilot database (read-only)

Predicts "adherence below 80% next week" per household-week (backend/app/adherence_features.py) with
scikit-learn's HistGradientBoostingClassifier. Gates: at least 30 real households AND 300 recorded
household-weeks; demo households are never used. Reports AUROC with a bootstrap 95% CI and calibration
(Brier score, reliability bins) in eval/adherence_model_results.json and eval/adherence_model_card.md.

Until a model passes the gates the reviewer sees nothing from it. A model that exists may only add a
reviewer-only "follow-up suggested" ordering hint in triage.py; it never creates or changes a finding
and is never shown to the family.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "backend" / ".env")

from app.adherence_features import FEATURES, household_weeks, vector  # noqa: E402

MIN_HOUSEHOLDS = 30
MIN_HOUSEHOLD_WEEKS = 300
RESULTS = ROOT / "eval" / "adherence_model_results.json"
MODEL = ROOT / "backend" / "data" / "adherence_model.joblib"


def collect(store) -> tuple[list[dict], int]:
    """Household-week rows from every REAL household (demo households excluded)."""
    rows, households = [], 0
    for p in store.list_patients():
        if p.is_demo:
            continue
        items = [it.model_dump() for it in store.list_items(p.id, confirmed_only=True)
                 if it.schedule and it.schedule_approved_at and not it.stopped and not it.set_aside]
        events = store.list_doses(p.id, since="0000-00-00")
        hw = household_weeks(events, items, p.age)
        if hw:
            households += 1
            rows += [{**r, "household": p.id} for r in hw]
    return rows, households


def gate(rows: list[dict], households: int) -> dict:
    status = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "households": households,
              "household_weeks": len(rows), "required_households": MIN_HOUSEHOLDS,
              "required_household_weeks": MIN_HOUSEHOLD_WEEKS, "features": list(FEATURES)}
    status["status"] = "ready" if households >= MIN_HOUSEHOLDS and len(rows) >= MIN_HOUSEHOLD_WEEKS else "in_progress"
    return status


def bootstrap_auc(y, p, n=1000, seed=7) -> tuple[float, float]:
    from sklearn.metrics import roc_auc_score
    rnd, scores = random.Random(seed), []
    idx = list(range(len(y)))
    for _ in range(n):
        s = [rnd.choice(idx) for _ in idx]
        ys = [y[i] for i in s]
        if len(set(ys)) < 2:
            continue
        scores.append(roc_auc_score(ys, [p[i] for i in s]))
    scores.sort()
    return scores[int(0.025 * len(scores))], scores[int(0.975 * len(scores)) - 1]


def train(rows: list[dict], status: dict) -> dict:
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import brier_score_loss, roc_auc_score
    # split by household so the same family is never in both train and test
    homes = sorted({r["household"] for r in rows})
    random.Random(7).shuffle(homes)
    test_homes = set(homes[: max(1, len(homes) // 4)])
    tr = [r for r in rows if r["household"] not in test_homes]
    te = [r for r in rows if r["household"] in test_homes]
    clf = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200, random_state=7)
    clf.fit([vector(r) for r in tr], [r["label"] for r in tr])
    y, p = [r["label"] for r in te], list(clf.predict_proba([vector(r) for r in te])[:, 1])
    lo, hi = bootstrap_auc(y, p)
    bins = []
    for b in range(5):
        members = [(yi, pi) for yi, pi in zip(y, p) if b / 5 <= pi < (b + 1) / 5 or (b == 4 and pi == 1)]
        if members:
            bins.append({"bin": f"{b / 5:.1f}-{(b + 1) / 5:.1f}", "n": len(members),
                         "mean_predicted": round(sum(m[1] for m in members) / len(members), 3),
                         "observed": round(sum(m[0] for m in members) / len(members), 3)})
    import joblib
    joblib.dump(clf, MODEL)
    return {**status, "status": "done", "train_rows": len(tr), "test_rows": len(te),
            "auroc": round(roc_auc_score(y, p), 3), "auroc_ci": [round(lo, 3), round(hi, 3)],
            "brier": round(brier_score_loss(y, p), 4), "calibration": bins}


def main(store=None) -> dict:
    if store is None:
        from app.store import Store
        store = Store()
    rows, households = collect(store)
    status = gate(rows, households)
    if status["status"] != "ready":
        RESULTS.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(f"Not training: {households} of {MIN_HOUSEHOLDS} real households and {len(rows)} of "
              f"{MIN_HOUSEHOLD_WEEKS} household-weeks. The reviewer sees nothing from this model.")
        return status
    try:
        result = train(rows, status)
    except ImportError:
        sys.exit("pip install -r eval/requirements-ml.txt (scikit-learn) first")
    RESULTS.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"AUROC {result['auroc']} (95% CI {result['auroc_ci'][0]}-{result['auroc_ci'][1]}), Brier {result['brier']}. "
          "Update eval/adherence_model_card.md before using it.")
    return result


if __name__ == "__main__":
    main()
