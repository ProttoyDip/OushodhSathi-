# API reference

Generated from the FastAPI app by [`backend/scripts/gen_docs.py`](../backend/scripts/gen_docs.py); do not edit by hand.
95 endpoints.

The interactive version with request and response schemas runs at `/docs` on the API (for example http://localhost:8000/docs).

**Who may call it**

- **public**: anyone (rate limits still apply).
- **family link**: the household's private key in the `X-Family-Key` header (the invented demo household needs none). A wrong key answers "not found", so household ids cannot be probed.
- **reviewer**: a personal reviewer token in `X-Reviewer-Token` (the shared demo token works only when `DEMO_MODE=true`).
- **admin token**: `ADMIN_TOKEN` in `X-Admin-Token`.

Webhook routes check the provider's signature themselves.

## Service

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `GET` | `/health` | public | Configured providers are reported by NAME only, never keys. |

## Households, medicines and findings

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `GET` | `/patients` | reviewer | Reviewer only. |
| `POST` | `/patients` | public | Creates a household after the family accepts the privacy notice. |
| `POST` | `/patients/{pid}/family-key/rotate` | family link | A new private link for the household. |
| `GET` | `/patients/{pid}/export` | family link | Everything the family can see, as one JSON file. |
| `DELETE` | `/patients/{pid}` | family link | The family deletes the household and everything about it. |
| `GET` | `/patients/{pid}` | family link |  |
| `GET` | `/patients/{pid}/items` | family link |  |
| `POST` | `/patients/{pid}/items` | family link |  |
| `PATCH` | `/items/{item_id}` | family link |  |
| `DELETE` | `/items/{item_id}` | family link |  |
| `POST` | `/patients/{pid}/check` | family link | Runs the deterministic rules on CONFIRMED items. |
| `GET` | `/patients/{pid}/status` | family link | Family-safe status: says whether a review is in progress, never what is pending. |
| `GET` | `/patients/{pid}/flags` | family link | view=family returns ONLY confirmed flags (AGENTS.md rule 2). |
| `GET` | `/patients/{pid}/reviews` | reviewer |  |
| `GET` | `/patients/{pid}/passport` | family link |  |
| `POST` | `/patients/{pid}/bp` | family link | JSON body {systolic, diastolic, taken_on?}; query parameters still work for automations. |
| `GET` | `/patients/{pid}/report` | family link |  |
| `POST` | `/patients/{pid}/scan` | family link | Photos -> shelf agent -> unconfirmed items. |
| `GET` | `/patients/{pid}/next-step` | family link | The one thing to do next. |
| `POST` | `/patients/{pid}/questions` | family link | A family question for the reviewing pharmacist. |
| `GET` | `/patients/{pid}/questions` | family link |  |
| `POST` | `/patients/{pid}/questions/seen` | family link |  |
| `POST` | `/patients/{pid}/seen` | family link | The family opened results or the passport; moves the next step along. |
| `PATCH` | `/patients/{pid}` | family link | Allergies, emergency contact and visit questions, entered by the family. |
| `POST` | `/patients/{pid}/allergies/confirm` | reviewer |  |
| `PATCH` | `/items/{item_id}/clinical` | reviewer | What it is for, and stopped: written by the pharmacist or doctor, never by AI. |
| `POST` | `/patients/{pid}/schedule/approve` | reviewer | The reviewer approves the times on the list. |
| `GET` | `/patients/{pid}/case-summary` | reviewer | AI summary for the reviewer, facts only; names are checked against the record. |
| `GET` | `/patients/{pid}/bp-trend` | reviewer | Reviewer only: straight-line trend of the last `days` of home readings with a 95% CI. |
| `POST` | `/patients/{pid}/bp/read` | family link | A photo of the BP monitor -> numbers for the family to check and save. |
| `POST` | `/patients/{pid}/emergency` | family link | Turns on (or renews) the emergency page behind the passport QR. |
| `GET` | `/patients/{pid}/emergency` | family link |  |
| `DELETE` | `/patients/{pid}/emergency` | family link |  |
| `GET` | `/patients/{pid}/fhir` | family link | FHIR R4 Bundle: Patient + one MedicationStatement per current medicine. |
| `GET` | `/patients/{pid}/today` | family link | Today's medicines from the APPROVED plan only. |
| `GET` | `/patients/{pid}/visit` | family link | Before the doctor visit: medicines, what changed since the last visit and who changed it, confirmed findings and notes, recent blood pressure, and the family's questions. |
| `POST` | `/patients/{pid}/visit/done` | family link | After the visit: start counting changes from now; the family scans the new prescription next. |
| `GET` | `/patients/{pid}/cleanup` | family link | Strips to set aside so nobody takes them by mistake: expired, or stopped by the reviewer. |
| `GET` | `/patients/{pid}/savings` | family link | Same generic, same strength, same form, lower demo reference price. |
| `POST` | `/patients/{pid}/ramadan-request` | family link | The family asks for a fasting review. |
| `DELETE` | `/patients/{pid}/ramadan` | family link | End of Ramadan (or a withdrawn request): back to the usual approved times. |
| `POST` | `/patients/{pid}/ramadan-approve` | reviewer | A pharmacist or doctor maps each medicine to sehri and/or iftar, with a note. |
| `GET` | `/patients/{pid}/activity` | family link | What happened in this household, for siblings far away: kinds and counts only. |
| `GET` | `/patients/{pid}/kidney` | reviewer | Reviewer only: the latest creatinine, its eGFR (CKD-EPI 2021) and KDIGO stage. |
| `POST` | `/patients/{pid}/kidney-tests` | reviewer | Reviewer only: a creatinine result (mg/dL or umol/L). |
| `POST` | `/patients/{pid}/doses` | family link | The family ticks a dose as taken or not taken. |
| `GET` | `/patients/{pid}/doses` | family link | The family's own ticks. |
| `GET` | `/patients/{pid}/adherence` | reviewer | Reviewer only: 14-day adherence per medicine with 95% Wilson intervals. |
| `GET` | `/patients/{pid}/start-notes` | reviewer | Possible omissions (START v3), for the doctor. |
| `GET` | `/patients/{pid}/calls/settings` | family link |  |
| `PUT` | `/patients/{pid}/calls/settings` | family link | The family turns on the daily call (with consent) or changes its time. |
| `DELETE` | `/patients/{pid}/calls/settings` | family link | Stop the calls at any time; the number is erased at once. |
| `POST` | `/patients/{pid}/calls/test` | family link | "Call now (test)". |
| `GET` | `/patients/{pid}/calls/current` | family link | The simulator page: the call that is ringing or in progress now, if any. |
| `GET` | `/patients/{pid}/calls` | reviewer | Reviewer only: recent check-in calls and the answer rate (95% Wilson interval). |
| `POST` | `/patients/{pid}/whatsapp/test` | family link | "Send now (test)". |
| `GET` | `/patients/{pid}/whatsapp/current` | family link |  |

## Reviewer queue and decisions

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `GET` | `/flags` | reviewer | Reviewer queue across patients: red first, then the higher-risk household, then longest waiting. |
| `POST` | `/flags/{flag_id}/review` | reviewer |  |
| `POST` | `/flags/{flag_id}/undo` | reviewer |  |
| `GET` | `/flags/{flag_id}/why` | reviewer | Reviewer only: the knowledge-graph path that explains a finding (brand -> generic -> class -> group / rule, each step with its source). |
| `POST` | `/flags/{flag_id}/opened` | reviewer |  |
| `GET` | `/reviewer/me` | reviewer | Who is signed in: shown in the dashboard and recorded on every decision. |

## Administration

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `POST` | `/admin/reviewers` | admin token | A personal login for one pharmacist or doctor. |
| `GET` | `/admin/reviewers` | admin token |  |
| `POST` | `/admin/reviewers/{rid}/revoke` | admin token |  |
| `POST` | `/admin/reviewers/{rid}/reissue` | admin token | A new invite link for the same person; the old one stops working. |
| `POST` | `/admin/patients/{pid}/family-key` | admin token | A family lost its link (new phone, cleared browser): a fresh link replaces the old one. |
| `POST` | `/admin/notify/weekly` | admin token | The weekly report email for every household that opted in; at most once per ISO week. |

## Sathi (in-app helper)

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `POST` | `/assistant/ask` | family link |  |
| `POST` | `/sathi/transcribe` | family link | Speech to text for Sathi's text box. |

## Daily check-in call

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `POST` | `/calls/sim/{aid}/answer` | family link |  |
| `POST` | `/calls/sim/{aid}/decline` | family link |  |
| `POST` | `/calls/sim/{aid}/press` | family link |  |
| `POST` | `/calls/run-due` | admin token | The cron (GitHub Actions, every 15 minutes) places due calls and the one retry, and sends the daily WhatsApp message to households that chose it. |
| `POST` | `/calls/webhook/{name}` | public | Provider callbacks. |

## Daily WhatsApp check-in

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `POST` | `/whatsapp/sim/{cid}/reply` | family link |  |
| `POST` | `/whatsapp/sim/{cid}/text` | family link |  |
| `GET` | `/whatsapp/webhook` | public | Meta's subscription check: echo hub.challenge when hub.verify_token matches WHATSAPP_VERIFY_TOKEN. |
| `POST` | `/whatsapp/webhook` | public | Taps and messages from WhatsApp. |

## Brands and research

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `GET` | `/brands/suggest` | public | "Did you mean?" for a brand the app did not recognise: up to three table brands, for the family to tap if one is what is printed. |

## Emergency page

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `GET` | `/emergency/{token}` | public | Read-only, no login: medicines, allergies and the emergency contact. |

## Evaluation (public numbers)

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `GET` | `/eval/results` | public | Summaries of eval/results_*.json. |
| `GET` | `/pilot/stats` | public | Pilot proportions with 95% Wilson intervals, from eval/pilot.csv (real households only). |
| `GET` | `/eval/sathi` | public | Summaries of eval/sathi_results_*.json, read by /docs and the README. |
| `GET` | `/eval/review-time` | public | Median minutes from opening a finding to deciding it: the cost of a review. |
| `GET` | `/eval/retrieval` | public | Sathi app-guide retrieval: recall@1 and recall@3 with 95% Wilson CIs for keyword, vector and hybrid search, from eval/help_retrieval_results.json (empty until the eval has run). |
| `GET` | `/eval/models` | public | Status of the escalate-only Sathi intent classifier and the missed-dose risk model, from their evaluation files. |

## AI models

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `GET` | `/models` | public | The model chain per task (first answers, the rest are fallbacks), the user's choice, and what actually answered last. |
| `PUT` | `/models/preference` | reviewer |  |

## Demo

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `POST` | `/demo/reset` | public | Fresh demo household for the next judge: some findings confirmed for the family view, some pending for the reviewer queue. |

## Other

| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `GET` | `/questions` | reviewer |  |
| `POST` | `/questions/{qid}/reply` | reviewer |  |
| `GET` | `/ramadan/requests` | reviewer | Fasting reviews waiting for a pharmacist or doctor, oldest first. |
