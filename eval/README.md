# Extraction eval

Measures how well the shelf agent reads real Bangladeshi medicine photos.
Every number we publish about extraction comes from `results_<prompt_version>.json`
produced here — nothing is typed in by hand.

## Add your own photos (target 30; numbers are published from 25)

1. Photograph real medicines at home, with permission. Mix the hard cases on purpose, about
   equally: strips **cut into pieces** (brand half missing), **glare** on foil or dim light,
   **Bangla** print on boxes, and **handwritten prescriptions**, plus a few clear ones.
2. **Privacy checklist** (every photo, before it goes into `eval/photos/`):
   - [ ] no face, hand with a ring or tattoo, or any person in the frame
   - [ ] no patient or doctor name, phone number, address or registration number visible
     (fold, cover or crop them; a prescription header usually has all of these)
   - [ ] no QR code or barcode that links to a person
   - [ ] the file name says nothing about the person (use `cut_01.jpg`, not `rahima_napa.jpg`)
3. Save the photos in `eval/photos/`.
4. Label them in the browser:

   ```
   backend/.venv/Scripts/python backend/scripts/label_photos.py     # Windows
   backend/.venv/bin/python backend/scripts/label_photos.py         # macOS / Linux
   ```

   It opens a local page (http://127.0.0.1:8765, nothing leaves the machine) showing one unlabelled
   photo at a time. Type one row per medicine visible: brand, strength and expiry (`YYYY-MM`) exactly
   as printed, leaving expiry empty if it is cut off, and pick the photo's condition. Saving requires
   the privacy tick. Rows go to `eval/labels.csv`:

   ```csv
   image_path,brand,strength,expiry,condition
   photos/cut_01.jpg,Napa,500 mg,2027-03,cut_strip
   photos/box_02.jpg,Seclo,20 mg,,bangla
   ```

**Two labelling rules.** Leave strength empty when the pack prints no dose strength (a syrup's "100 ml"
or a spray's "120 metered sprays" is not a strength); such rows are left out of the strength score. A brand
printed in both scripts may be labelled with both spellings, `Nasovap|ন্যাসোভ্যাপ`, so a correct read in either
script counts. `label_photos.py --drafts FILE` pre-fills suggested labels, but every photo is still checked
and saved by hand.

## Real handwritten prescriptions from a public dataset

Handwritten prescriptions are hard to collect with consent, so the eval can also use a public dataset:
Badhon D.R. et al., "Image-to-Text Bilingual Dataset from Medical Prescriptions", Mendeley Data, V2, 2026, [doi:10.17632/tg2hm7n2bs.2](https://doi.org/10.17632/tg2hm7n2bs.2), licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

1. Unzip the dataset into `eval/raw/prescriptions_bd/` (git-ignored: the full dataset is never committed).
2. Run `backend/.venv/Scripts/python backend/scripts/pick_prescriptions.py`. It opens a local page
   (http://127.0.0.1:8766) with 20 prescriptions whose transcription names brands from our tables,
   chosen to cover as many brands as possible. Tick up to 10.
3. For each one, confirm the brand(s) and strength(s) as written (expiry stays empty, condition
   "handwritten"), drag rectangles over every patient name, doctor name, phone, address, registration
   number or QR code, and tick the privacy check. Nothing is saved without the tick.
4. Only the redacted copy is written, as `eval/photos/rx_mendeley_XX.jpg` (no metadata), with its rows
   in `eval/labels.csv` marked `source=mendeley:tg2hm7n2bs`.

`run_eval.py` reports these photos separately from our own (`by_source`), so every number says where it
came from. They count as real photos (they are real prescriptions), not as synthetic.

## Run

Configure at least one vision provider in `backend/.env`, then from the repo root:

```
backend/.venv/Scripts/python eval/run_eval.py                  # the vision chain, as the app runs it
backend/.venv/Scripts/python eval/run_eval.py --per-provider   # also each vision provider on its own
```

It writes `eval/results_<prompt_version>.json` with, each as a proportion with a 95% Wilson interval:
brand read correctly, brand and strength correct, brand and expiry correct (rows with a labelled
expiry), and the **needs-check rate** (correctly found medicines below the app's 0.75 confidence
cut-off, which the app shows for a human check). It also writes a **reliability table** (stated
confidence vs observed accuracy, to check that cut-off) and results per photo condition. With fewer
than 25 photos the file says "evaluation in progress (n = ...)" and `/docs` and the README show only
that. Never type a number by hand.

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
