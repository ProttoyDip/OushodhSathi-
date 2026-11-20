# Data sources and licences

OushodhSathi's safety rules run on **reference tables** in [`backend/data/`](../backend/data). Every row
carries its source, every rule cites the table it used, and a curated row always wins over a bulk-imported one.

## Reference tables

| Table | Rows | What it is | Status |
| --- | --- | --- | --- |
| [`brands_seed.csv`](../backend/data/brands_seed.csv) | 30 | Curated Bangladeshi brands with generic and drug class | Demo seed, **not yet pharmacist-verified**; always takes priority |
| [`brands_full.csv`](../backend/data/brands_full.csv) | 13,622 | Every brand in the *Medicinal Products in Bangladesh* dataset (University of Dhaka, 2024) | Imported, **not pharmacist-verified**; used for matching and suggestions |
| [`brands_bn.csv`](../backend/data/brands_bn.csv), [`generics_bn.csv`](../backend/data/generics_bn.csv) | 27, 19 | Bangla spellings of brands and generics | Spelling table; a cut-off fragment is never guessed |
| [`interactions_seed.csv`](../backend/data/interactions_seed.csv) | 6 | Drug–drug interactions that matter most for hypertension and diabetes | Curated seed, **pharmacist review pending** |
| [`beers_seed.csv`](../backend/data/beers_seed.csv) | 5 | Medicines to avoid after 65 (AGS Beers Criteria 2023) | Seed |
| [`acb_seed.csv`](../backend/data/acb_seed.csv) | 40 | Anticholinergic Cognitive Burden scores | Seed; permission to request before commercial use |
| [`aware_2025.csv`](../backend/data/aware_2025.csv) | 21 | WHO AWaRe antibiotic groups (Access / Watch / Reserve) | Seed to verify against the WHO spreadsheet; non-commercial licence |
| [`renal_seed.csv`](../backend/data/renal_seed.csv) | 2 | Kidney-function dose thresholds (metformin, FDA 2016) | Sourced rows only |
| [`duplicate_classes.txt`](../backend/data/duplicate_classes.txt), [`class_groups.csv`](../backend/data/class_groups.csv) | 8, 6 | Drug classes where two members are a duplication; groups for the "triple whammy" | Curated |
| [`stopp_start.csv`](../backend/data/stopp_start.csv) | 0 | STOPP/START v3 criteria | Engine ready; criteria to be entered and verified by our pharmacist |

## How the national brand list is used

Bangladesh has well over ten thousand registered brands, so a hand-made table cannot cover a real household.

- **Import.** [`backend/scripts/import_brands.py`](../backend/scripts/import_brands.py) turns the public dataset
  into `brands_full.csv`: one row per brand, keeping the tablet or capsule row when a brand has several forms.
  Every row is marked `verified=no` and credits the dataset.
- **Salt names.** When the table loads, a registered name such as "azithromycin dihydrate" is reduced to the
  base name the rules use ("azithromycin"), but only when that base is a generic the app already knows
  ([`generic_names.py`](../backend/app/generic_names.py)). "Potassium chloride" stays as it is, and creams or
  eye drops are never merged with tablets.
- **Drug classes.** A dataset brand whose base generic is exactly a curated generic takes the curated drug class
  (1,893 brands). So a curated brand and a dataset brand of the same medicine (Zimax and Azithrocin) are flagged
  as a double dose, and a dataset antibiotic is checked like a curated one.
- **Priority.** Curated rows always win, so the safety rules keep their reviewed classes.

## Licences and credits

- **Code:** MIT, see [`LICENSE`](../LICENSE).
- **DDInter 2.0** drug–drug interaction database, [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Used for non-commercial prototype purposes with attribution; [`backend/scripts/import_ddinter.py`](../backend/scripts/import_ddinter.py) imports its downloads. The repository ships only a small curated interaction seed.
- **AGS Beers Criteria** (American Geriatrics Society) as the clinical reference for the 65+ rules in [`backend/data/beers_seed.csv`](../backend/data/beers_seed.csv).
- **"Medicinal Products in Bangladesh — A Dataset of Generic and Brand Names, Dosage Strengths, and Manufacturers"**, Md Mahmudur Rahman and Md M Khan, University of Dhaka, Mendeley Data, v1, 2024, [doi:10.17632/zhtvkny53n.1](https://data.mendeley.com/datasets/zhtvkny53n/1). Licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). [`backend/data/brands_full.csv`](../backend/data/brands_full.csv) (13,622 brands) is derived from it by [`backend/scripts/import_brands.py`](../backend/scripts/import_brands.py): one row per brand (the tablet or capsule row where a brand has several forms), brand, generic and manufacturer only. When it loads, a dataset generic such as "azithromycin dihydrate" is reduced to the base name the rules use (`backend/app/generic_names.py`, only when that base is a generic the app already knows), and takes the seed's drug class when the base is exactly a seed generic, so a seed brand and a dataset brand of the same medicine are flagged as a double dose. Its rows are not pharmacist-verified, and the curated seed (`brands_seed.csv`) always takes priority, so the safety rules keep their curated drug classes. The original download is never committed (`backend/data/raw/` is git-ignored).
- **Handwritten prescription photos** in the strip-reading eval: Badhon D.R. et al., "Image-to-Text Bilingual Dataset from Medical Prescriptions", Mendeley Data, V2, 2026, [doi:10.17632/tg2hm7n2bs.2](https://doi.org/10.17632/tg2hm7n2bs.2), licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Only prescriptions we selected are used, with patient and doctor details blacked out before they are copied into `eval/photos/` (`rx_mendeley_*.jpg`, rows marked `source=mendeley:tg2hm7n2bs`); the full dataset is never committed. Results are reported per source, and `/docs` credits the dataset wherever its photos count.
- **Brand seed** [`backend/data/brands_seed.csv`](../backend/data/brands_seed.csv): demo data, **not pharmacist-verified**.
- **WHO AWaRe classification 2025** ([B09489](https://www.who.int/publications/i/item/B09489)) for antibiotic groups in [`backend/data/aware_2025.csv`](../backend/data/aware_2025.csv): **CC BY-NC-SA 3.0 IGO, non-commercial.** The shipped file is a seed to verify; [`scripts/import_aware.py`](../backend/scripts/import_aware.py) converts the official spreadsheet. A commercial service needs WHO's permission or another source.
- **Anticholinergic Cognitive Burden scale** (2012 update, Aging Brain Care) in [`backend/data/acb_seed.csv`](../backend/data/acb_seed.csv): the scale's owners ask users to request permission; to be requested before commercial use.
- **STOPP/START version 3**: O'Mahony D et al., Eur Geriatr Med 2023;14(4):625-632, [doi:10.1007/s41999-023-00777-y](https://doi.org/10.1007/s41999-023-00777-y). Cited; criteria are entered and verified by our pharmacist, none are shipped.
- **Kidney rules**: 2021 CKD-EPI equation (National Kidney Foundation, NIDDK); metformin thresholds from the FDA Drug Safety Communication of 8 April 2016; triple whammy from Medsafe NZ (2013), Lapi et al. (BMJ 2013) and Harezlak et al. (Adv Ther 2022). Sources are in the code and in each data row.
- **Fonts:** Schibsted Grotesk, Anek Bangla, Instrument Sans and Hind Siliguri, all under the SIL Open Font License.
