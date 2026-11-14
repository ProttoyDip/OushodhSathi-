# Model card: Sathi intent classifier (escalate-only)

**Status: evaluation in progress. Switched off (`SATHI_INTENT_MODEL=off`).** No accuracy is claimed.

## What it is for
Catching medical questions that slip past `backend/app/guard.py`'s word lists (Banglish, typos) so they go to
a pharmacist instead of the app guide.

## Safety contract
- Runs after `guard.py`, only on questions the guard did not already route to a human.
- Can only move a question towards **medical** or **emergency**. It can never move one to **app**.
- If it is off, missing, slow (3 s timeout) or failing, Sathi behaves exactly as without it.
- It never creates, removes or grades a medicine finding (AGENTS.md rule 1), and patient names are
  removed before the question is embedded.

## Deployed model
- Embeddings: `baai/bge-m3` through NVIDIA's API (`https://integrate.api.nvidia.com/v1/embeddings`,
  [model page](https://build.nvidia.com/baai/bge-m3)), 1024 dimensions, 100+ languages. Bengali coverage must be
  confirmed by the held-out evaluation below, not assumed.
- Classifier: scikit-learn logistic regression (`class_weight="balanced"`), trained offline by
  `eval/train_intent_model.py`, saved as coefficients only in `backend/data/intent_model.json`.

## Research model (not deployed)
`csebuetnlp/banglabert` fine-tuned in `eval/train_banglabert.ipynb` (Colab). Reported next to the deployed
model for comparison only.

## Data
- `eval/intent_dataset.csv`: `text, label (app | medical | emergency), lang, source, split`.
- Started from the 78 app/medical/emergency cases of `eval/sathi_cases.csv` (held-out).
- The **held-out split is written by people only**. LLM paraphrases may be added to the train split only,
  marked `source=synthetic` (`eval/add_intent_example.py --synthetic`).

## Gates before switching it on
1. At least **200 human-written held-out examples**.
2. `eval/run_intent_eval.py`: per-class recall with 95% Wilson intervals, and **medical recall not lower than
   guard.py alone** (100% on `sathi_cases.csv` today).
3. The Sathi eval in CI stays at 100% for medical and emergency.

## Results
| Model | App recall | Medical recall | Emergency recall | Held-out n |
| --- | --- | --- | --- | --- |
| Deployed (bge-m3 + logistic regression) | evaluation in progress | evaluation in progress | evaluation in progress | 78 of 200 |
| Research (BanglaBERT) | not run yet | not run yet | not run yet | — |
