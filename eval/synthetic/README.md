# Synthetic eval set (NOT real photos)

Every image here was drawn in code (`make_synthetic.py`): HTML rendered by headless Chrome, then
photo-like damage (rotation, blur, noise, JPEG, glare, torn cut edges, perspective). Each image
carries a small "SYNTHETIC" mark. There are no real packs, logos, manufacturer names, people,
prescriptions or patient details. Brand names and strengths come from `backend/data/brands_seed.csv`;
Bangla names from `backend/data/brands_bn.csv`.

## What is here

| Set | Count | Label file |
|---|---|---|
| Medicine photos (`photos/`) | 30 photos, 45 label rows | `labels.csv` (`image_path,brand,strength,expiry,condition`) |
| BP monitor screens (`bp_photos/`) | 20 photos, 3 machine looks, clear / angled / glare | `bp_labels.csv` (`image_path,systolic,diastolic,pulse`) |

Medicine photos by condition: 8 cut strips, 6 glare (2 with two medicines), 5 Bangla print,
5 typed-handwriting prescriptions (2–3 medicines each, header blacked out), 6 clear (2 shelf
photos with 3 medicines, combinations such as Napa Extra, Osartil Plus, Amdocal Plus included).
Expiry is labelled where the EXP text is in the picture (25 rows); it is left empty on cut-off
pieces and prescriptions.

## How to report it

This is a **synthetic benchmark**. It tests the pipeline and compares providers and prompt
versions; it does **not** measure accuracy on real phone photos. Never publish its numbers as
real-world accuracy, and keep it out of `eval/labels.csv` and `eval/bp_labels.csv`, which
`/docs` reads as real-photo results. Run it with `sh eval/run_synthetic.sh` (or
`powershell -File eval/run_synthetic.ps1` on Windows; add `--per-provider` / `-PerProvider` to also
test each vision provider alone). Results go to `eval/synthetic/results_<prompt>.json` and
`eval/synthetic/bp_results_<prompt>.json`, carry `"kind": "synthetic"`, and appear on `/docs` only in
their own "Synthetic benchmark" card, below the real-photo results. A synthetic run refuses to write
a real results file.

## Regenerate (optional)

`python make_synthetic.py OUT_DIR` (needs Playwright with Chrome, Pillow, and the fontsource
packages for Noto Sans Bengali, Caveat and Roboto Condensed). The random seed is fixed, so the same
images come out every time. It is optional: the images are committed, and the script is not part of
the backend package or CI. Before running it, point `FONTS` at the top of the script to where the
fontsource packages are unpacked on your machine (it is set to the folder it was built in).
