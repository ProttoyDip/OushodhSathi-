# Model card: missed-dose risk model (reviewer-only)

**Status: not trained. There is no real pilot data yet.** The reviewer sees nothing from this model.

## What it is for
Suggesting which households a pharmacist might follow up first: those whose adherence is likely to fall
below 80% next week. A queue-ordering hint only.

## What it may never do
- Create, remove or change a finding (AGENTS.md rule 1).
- Appear in the family app, an email or the passport.
- Train or run on the invented demo household.

## Data and features
One row per household-week from the family's taken / not-taken ticks (`dose_events`), built by
`backend/app/adherence_features.py`: adherence over the previous two weeks and how many doses were recorded,
number of approved medicines, doses per day, number of prescribers, age, and the share of noon doses.
Label: adherence in the following week below 80% (with at least 5 ticks that week).

## Model
scikit-learn `HistGradientBoostingClassifier` (max depth 3), trained offline by
`eval/train_adherence_model.py`, split by household so a family is never in both train and test.

## Gates before it is used
1. At least **30 real households** and **300 household-weeks** (the script refuses otherwise).
2. AUROC reported with a bootstrap 95% CI, plus calibration (Brier score and reliability bins).
3. A person on the team reads this card, fills in the results below and decides to use it.

## Results
| Households | Household-weeks | AUROC (95% CI) | Brier | Calibration |
| --- | --- | --- | --- | --- |
| not enough data yet | — | — | — | — |
