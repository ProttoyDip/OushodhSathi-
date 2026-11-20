# Evaluation

What we have measured, how, and what we have not measured yet. Every number on this page comes from a results
file in [`eval/`](../eval) produced by a script in the same folder; nothing is typed in by hand. The landing
page, `/docs` and the submission text are generated from the same files, and tests fail if they drift.

## Principles

- **Real and synthetic results are never mixed.** Real-photo results come from photos of real medicines.
  The synthetic benchmark uses computer-drawn images to test the pipeline; it lives in
  [`eval/synthetic/`](../eval/synthetic), is labelled `"kind": "synthetic"`, and is never reported as accuracy.
- **Every proportion has a 95% confidence interval** (Wilson score interval), because our samples are small.
- **No accuracy is claimed below 25 labelled photos.** Below that, results files say "evaluation in progress".
- **Prompts are versioned.** Each results file names the prompt version and model that produced it
  (`results_extract_strip.v3.json` is prompt v3). Changing a prompt means a new file and a new run.
- **Weak spots are reported, not hidden.** Results are broken down by photo condition so a good average
  cannot cover a failing case.

## 1. Reading medicine photos (real photos)

**Data.** 40 photos of the team's own medicines (`eval/photos/own_01.jpg` to `own_40.jpg`): blister strips, boxes,
bottles and tubes, from 29 different products. Every photo was privacy-checked (no faces, names, phone
numbers or addresses), resized to 2,000 px and stripped of metadata.

**Labels.** [`eval/labels.csv`](../eval/labels.csv): brand, strength and expiry exactly as printed, plus the
photo's condition (`clear`, `glare`, `cut_strip`, `bangla`). A brand printed in both scripts may list both
spellings (`Nasovap|ন্যাসোভ্যাপ`) so a correct read in either counts. Strength is left empty when the pack
prints no dose strength (a syrup's "100 ml" is not a strength); expiry is left empty unless it is clearly
printed. Those empty fields are not scored.

> **How the labels were made.** A vision model drafted them; an AI coding assistant then checked every draft
> against its photo and changed one. They have not yet been re-checked by a person. Anyone can do that with
> `backend/scripts/label_photos.py`, and the results should be re-run afterwards.

**Results** (prompt `extract_strip.v3`, the live model chain, [`results_extract_strip.v3.json`](../eval/results_extract_strip.v3.json)):

| Measure | Result | 95% CI |
| --- | --- | --- |
| Brand read correctly | **35 / 40 (88%)** | 74%–95% |
| Strength read correctly | **24 / 28 (86%)** | 69%–94% |
| Expiry read correctly | 1 / 1 | (too few printed expiries to say) |

| Photo condition | Brand correct |
| --- | --- |
| Clear | 19 / 19 |
| Glare | 12 / 14 |
| Cut strip | 3 / 3 |
| **Printed only in Bangla** | **1 / 4: our weak spot** |

**What fails.** Stylised Bangla logos on cough syrups and herbal products are read as other Bangla words
(for example "বাসক" read as "জ্যান্টিল"). Two glare photos lose letters ("Ebanex" read as "Ebanine",
"Finix" as "Fimx"). One strength lacked its unit ("300" for "300 mcg"), and one combination strength was
returned with the ingredient names.

**Previous prompt.** Prompt v2 on the same photos: brand 34 / 40 (85%, 95% CI 71%–93%), strength 23 / 28 (82%).
With each vision provider alone (v2 run): NVIDIA Nemotron brand 35 / 40 and strength 25 / 28; the free
OpenRouter models mostly returned no answer because of rate limits, which is reported as "no answer", not
as an accuracy figure. The v2 → v3 difference is one photo and is within the confidence intervals.

**Confidence calibration.** Of the 28 readings the model gave a confidence of 0.9 or more, 26 were correct
(93%). Readings under 0.75 are always shown to a person to check, whatever their accuracy.

Reproduce: `backend/.venv/Scripts/python eval/run_eval.py` (Windows) or `backend/.venv/bin/python eval/run_eval.py`.
Add `--per-provider` to score each vision provider alone.

## 2. Synthetic benchmark (computer-drawn images; not real-photo accuracy)

Thirty computer-drawn medicine images with 45 medicines, and 20 drawn blood-pressure monitor screens, in
[`eval/synthetic/`](../eval/synthetic). They test the pipeline end to end and let us compare providers cheaply.

| Measure | Result | 95% CI |
| --- | --- | --- |
| Brand | 40 / 45 (89%) | 76%–95% |
| Expiry | 19 / 25 (76%) | 57%–88% |
| Blood pressure, systolic exact | 20 / 20 | |
| Blood pressure, diastolic exact | 20 / 20 | |

It also showed overconfidence on drawn images: 3 of the model's 5 misreads came with a confidence of 0.9 or
more. That is why every reading is checked by the family before it is saved, and every finding by a clinician.

## 3. Sathi, the in-app helper (safety)

[`eval/run_sathi_eval.py`](../eval/run_sathi_eval.py): 83 written questions in Bangla, Banglish and English,
run through the guard and the guide search alone, with no language model (exactly as CI runs it).

| Category | Correct | Meaning of correct |
| --- | --- | --- |
| Medical questions | **33 / 33** | sent to a pharmacist, never answered by the app |
| Emergencies | **10 / 10** | the fixed "call 999 or go to hospital" card |
| Attempts to break the rules | **5 / 5** | refused |
| App questions | 34 / 35 (97%) | answered from the right guide entry; the miss went to the pharmacist (the safe direction) |

CI fails if any medical or emergency question ever receives an app answer. The cases were written by the
team and still need a native speaker's review.

## 4. Help search (retrieval)

[`eval/run_retrieval_eval.py`](../eval/run_retrieval_eval.py), 79 questions, recall@1 (the right guide entry first):

| Method | Recall@1 |
| --- | --- |
| Keyword (RapidFuzz) | 90% |
| Vector (NVIDIA `nemotron-3.5-embed-1b`) | 94% |
| **Hybrid (both, reciprocal rank fusion)** | **95% (75 / 79, 95% CI 88%–98%)** |

78 of the 79 questions were drafted by the build agent and still need the team's review.

## 5. Reviewer case summary (safety checks)

[`eval/run_case_summary_eval.py`](../eval/run_case_summary_eval.py): 10 uncached runs per version on the demo
household, free models. A run passes only if every safety check passes (no advice, no doses, no diagnoses,
no medicine or prescriber that is not in the record; for v2, every sentence cites a graph fact).

| Version | Passed every check | Median time |
| --- | --- | --- |
| v1 | 8 / 10 (95% CI 49%–94%) | 18 s |
| v2 (Graph RAG) | 8 / 10 (95% CI 49%–94%) | 42 s |

This measures safety and grounding, not usefulness; usefulness needs pharmacists.

## 6. Software tests

**444 automated tests** (`pytest` in `backend/`), run with the frontend lint and build on every push by
GitHub Actions. They cover:

- the rules engine, including combination medicines and same-medicine-across-salt-names
- the rule that the family only ever sees confirmed findings
- Sathi's guard
- the knowledge graph
- both check-in channels
- the database layer on SQLite and Postgres
- that the generated docs, landing numbers and check-in texts match the code

## Not measured yet

- **Pilot.** No real households yet. [`eval/pilot.csv`](../eval/pilot.csv) is ready; demo data is never counted.
- **Blood pressure from real monitor photos.** [`eval/run_bp_eval.py`](../eval/run_bp_eval.py) is ready; no labelled photos yet.
- **Handwritten prescriptions.** The pipeline can include selected, anonymised prescriptions from a public
  dataset (see [`DATA.md`](DATA.md)); none are in the scored set yet.
- **Review time** is recorded for every decision on the live system; there are no pilot reviews to report.
- **Two models are switched off by design** until real data exists: an intent classifier that can only make
  Sathi more cautious (needs 200+ human-written examples), and a missed-dose risk model (needs 30 real
  households). See their model cards in [`eval/`](../eval).
