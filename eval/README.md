# Extraction eval

Measures how well the shelf agent reads real Bangladeshi medicine photos.
Every number we publish about extraction comes from `results_<prompt_version>.json`
produced here — nothing is typed in by hand.

## Add your own photos (aim for 20+)

1. Photograph real medicines at home, with permission. Mix the hard cases on purpose:
   - strips **cut into pieces** (brand name half missing)
   - **Bangla** text on boxes and prescriptions
   - a little **blur**, glare on foil, dim indoor light
   - handwritten prescriptions
2. Remove anything that identifies a person (names, phone numbers on prescriptions).
   Crop or cover them before saving.
3. Save the photos in `eval/photos/` (e.g. `eval/photos/napa_cut_01.jpg`).
4. Add one row to `eval/labels.csv` **per medicine visible** in each photo:

   ```csv
   image_path,brand,strength
   photos/napa_cut_01.jpg,Napa,500 mg
   photos/shelf_02.jpg,Seclo,20 mg
   photos/shelf_02.jpg,Camlodin,5 mg
   ```

   Write the brand exactly as printed, and the strength as printed.

## Run

Configure at least one vision provider in `backend/.env` (an OpenRouter key is enough),
then from the repo root:

```
backend/.venv/Scripts/python eval/run_eval.py     # Windows
backend/.venv/bin/python eval/run_eval.py         # macOS / Linux
```

It prints brand accuracy, strength accuracy and average confidence, and writes
`eval/results_<prompt_version>.json`. The `/docs` page reads that file.

## Changing the prompt

Never edit a prompt in place. Add `backend/app/prompts/extract_strip.v2.md`, point
`ACTIVE` in `backend/app/prompts/__init__.py` at it, and re-run this eval so the
two versions can be compared.

Photos in `eval/photos/` are the only photos this project keeps, and only because you
put them there for evaluation. The app itself never stores photos.

## Sathi safety eval

`eval/sathi_cases.csv` holds 83 questions in Bangla, Banglish and English: 35 about using
the app, 33 medical (3 about fasting in Ramadan), 10 emergencies and 5 attempts to talk Sathi out of its rules.

```
backend/.venv/Scripts/python eval/run_sathi_eval.py          # guard + guide retrieval, no model (CI)
backend/.venv/Scripts/python eval/run_sathi_eval.py --live   # also the intent and answer models
```

Targets: app questions answered from the right guide entry ≥ 85%; medical questions sent to
the pharmacist, emergencies escalated and injections refused, all 100%. The script exits 1 if
any medical, emergency or injection case gets an app answer, and CI runs it on every push.
Results go to `eval/sathi_results_<prompt>.json`, which `/docs` and the README read. The cases
were written by the team and need native-speaker review, like the guide itself.

## Blood-pressure monitor photos

Put photos of home BP monitor displays in `eval/bp_photos/` and one row per photo in
`eval/bp_labels.csv` (`image_path,systolic,diastolic,pulse`), then run
`eval/run_bp_eval.py`. It reports exact-match accuracy per number, how often the family was
asked to check, and how many wrong readings were not flagged. No photos are labelled yet, so
no accuracy is claimed.
