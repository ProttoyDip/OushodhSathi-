# Features

Every feature of OushodhSathi, grouped by who uses it, with where it lives in the app and in the code.
Status words mean exactly this:

- **live**: works on the hosted site.
- **simulator**: the full flow runs in the browser, but the outside service (phone network, WhatsApp) is not connected yet.
- **ready, off**: built and tested, but switched off until real data or an account exists.

For the API behind each feature see [`API.md`](API.md); for the settings that switch things on see
[`CONFIGURATION.md`](CONFIGURATION.md).

The safety rules that every feature follows are in [`AGENTS.md`](../AGENTS.md):

- the rules engine alone creates findings;
- the family sees only clinician-confirmed findings;
- nothing tells anyone to stop, start or change a medicine;
- names and phone numbers never reach a model;
- full photos are never stored.

---

## 1. For the family

### Starting and privacy

| Feature | What it does | Where | Code | Status |
| --- | --- | --- | --- | --- |
| Create a household | Name, age, conditions; a required consent tick linked to the privacy notice; optional email with opt-in. Shows a "save your family link" step after. | `/start` | `frontend/src/app/(family)/start`, `POST /patients` | live |
| Private family link | Each household opens only with its random key; any other key answers "not found", so ids cannot be guessed. | `/p/{id}?key=…` | `backend/app/main.py` (`family_access`), `frontend/src/lib/familyKey.ts` | live |
| My households | Households this browser has opened are listed on the landing page, so a returning family does not create a second one. | `/` | `frontend/src/lib/familyKey.ts` | live |
| Data rights | Rotate the link (the old one stops at once), export everything as JSON (confirmed findings only), delete the household (typed confirmation). | `/p/{id}/settings` | `POST …/family-key/rotate`, `GET …/export`, `DELETE /patients/{id}` | live |
| Bangla ⇄ English, light ⇄ dark | Every page has both switches; Bangla first. | everywhere | `frontend/messages/bn.json`, `en.json` | live |

### Scanning medicines

| Feature | What it does | Where | Code | Status |
| --- | --- | --- | --- | --- |
| Scan strips, boxes, prescriptions | Up to 12 photos at once; a vision model reads brand, strength, expiry, prescriber and its own confidence. | `/p/{id}/scan` | `backend/app/agent.py` (Pydantic-AI agent), `backend/app/llm_router.py` | live |
| Photo-quality warning | Flags a photo as blurry, glare, too dark or too small before it is sent, using image statistics in the browser (no model; the photo does not leave the phone for this). Warns only, never blocks. | `/p/{id}/scan` | `frontend/src/lib/photoQuality.ts` | live |
| OCR second reader | A dedicated OCR model (NVIDIA `nemotron-ocr-v2`, PaddleOCR fallback) re-reads each photo; if the strength or expiry it sees disagrees with the vision model's reading, the item is marked "please check" with what it saw. Never changes a reading or creates a finding. | confirm screen | `backend/app/ocr_check.py` | live with an NVIDIA key |
| Brand → generic | Exact match, then strict fuzzy (ratio ≥ 88), over the 30 curated brands and the 13,622 brands of the national *Medicinal Products in Bangladesh* dataset (curated rows win); Bangla-script names match through a spelling table; a cut-off fragment is never guessed. See [`DATA.md`](DATA.md). | automatic | `backend/app/brands.py` | live |
| Unknown-brand lookup | Searches Bangladeshi medicine sites with Tavily (Perplexity only if `WEB_LOOKUP` lists it); the answer must cite a source and stays marked "found on the web, not verified". | automatic | `backend/app/research.py` | live with keys |
| "Is it one of these?" | For a brand the app did not recognise, up to three table brands to tap: spelling matching (typos, cut-off names) fused with embeddings (other scripts, generic names). A tap fills in the name as if typed. | `/p/{id}/confirm` | `backend/app/brand_suggest.py`, `GET /brands/suggest` | live |
| Confirm the list | The family checks each card; anything under 0.75 confidence, web-matched or flagged by the second reader is dashed and says "please check". Edit, add by hand, set the times of day, and say where each medicine came from. | `/p/{id}/confirm` | `frontend/src/components/StripCard.tsx` | live |
| Hide the name on prescriptions | The scan page asks families to fold or cover the patient's name before photographing a prescription. Photos with a prescription get no thumbnail. | `/p/{id}/scan` | `backend/app/agent.py` | live |

### After the pharmacist's review

| Feature | What it does | Where | Status |
| --- | --- | --- | --- |
| Status | Says whether a review is in progress, never what is pending. | `/p/{id}/status` | live |
| Results | Only clinician-confirmed findings, in plain Bangla, with the pharmacist's note and a fixed safety sentence. | `/p/{id}/results` | live |
| Today's medicines | Morning / noon / night as pictures, the strip's own photo, tablets drawn as shapes, a Listen button (browser voice), a printable fridge sheet. Only pharmacist-approved times appear; each dose is ticked taken / not taken (never advice to take it late or double it). | `/p/{id}/today` | live |
| Set aside | Expired strips and medicines the reviewer stopped, so nobody takes them by mistake. | `/p/{id}/cleanup` | live |
| Before the doctor visit | One printable page: what changed and who changed it, confirmed findings, four weeks of blood pressure, the family's questions. | `/p/{id}/visit` | live |
| Questions for the pharmacist | The family writes a question; the reviewer answers it. | `/p/{id}/questions` | live |
| Weekly report | A summary of the week (also by email for families who opted in). | `/p/{id}/report` | live |
| Medicine passport | A printable A5/A6 card grouped by time of day, with generic names large, confirmed notes, allergies and a QR code. | `/passport/{id}` | live |
| Emergency page | The passport's QR opens a read-only page with no login and first name only; the family can renew or switch it off. | `/e/{token}` | live |
| Blood pressure | Typed readings, or read from a photo of the monitor (the family checks the numbers; the photo is not stored). | `/p/{id}` | live |
| Same medicine, lower price | Compares only identical generic, strength and form, never switches a brand, and sends the question to the pharmacist. | `/p/{id}` | live (demo prices) |
| Ramadan | The family asks; a pharmacist or doctor maps each medicine to sehri or iftar; only then does Today's medicines change, with a fixed safety card. | `/p/{id}` | live |
| For siblings abroad | A shared activity log and a Bangla + English WhatsApp digest with the read-only emergency link. | `/p/{id}` | live |
| FHIR export | The confirmed list as a FHIR R4 Bundle. | `GET /patients/{id}/fhir` | live |

### Daily check-ins

The family chooses a channel in Settings, gives recorded consent and picks a time. Both channels share:

- **Timing:** quiet hours (no messages 21:00–08:00) and a stop switch that erases the number at once.
- **Records:** answers become dose ticks marked with their source.
- **Safety:** an emergency branch with the fixed 999 message and an alert to the family contact. No AI and no advice anywhere in either channel.

Full setup guide: [`CHECKINS.md`](CHECKINS.md).

| Feature | What it does | Where | Code | Status |
| --- | --- | --- | --- | --- |
| Daily Bangla phone call (IVR) | Recorded Bangla prompts: press 1 taken, 2 not taken, 9 emergency, for each approved slot. One retry after 15 minutes, a daily cap. | `/p/{id}/call`, `/call-demo` | `backend/app/voice_calls/` | simulator |
| Daily WhatsApp message | One approved template a day (all taken / something missed / emergency), then free follow-ups per slot inside WhatsApp's 24-hour window. Typed text is never stored or sent to a model; only emergency words get the 999 reply. | `/p/{id}/call` | `backend/app/whatsapp_checkin/` | simulator |
| Call audio | Seven prompts generated once, with digits spoken as words. Draft voice: Meta MMS-TTS, non-commercial licence. Azure bn-BD supported. | `frontend/public/audio/call/` | `backend/scripts/make_call_audio.py` | draft, needs a native speaker's check |

### Sathi (সাথী), the in-app helper

| Feature | What it does | Code | Status |
| --- | --- | --- | --- |
| Next step | Always shows the one next thing to do, chosen by a state machine (not AI). | `backend/app/next_step.py` | live |
| App-guide answers | Answers "how do I…" only from the written guide in `docs/help`, found by contextual hybrid search (keywords + vectors in pgvector, fused by reciprocal rank). | `backend/app/sathi.py`, `help_index.py`, `help_vectors.py` | live |
| Medical questions go to a person | A guard runs before and after every model call; medical intent (or unsure) goes to the pharmacist; emergency words get a fixed "call 999" card with no AI. | `backend/app/guard.py` | live |
| Voice input | Bangla speech to text with Whisper large-v3 (NVIDIA), or the browser's own; the transcript lands in the box to check before sending; audio is never stored. | `backend/app/asr.py` | live with a key |
| Read aloud | Answers and Today's medicines can be read out with the phone's own Bangla voice. | `frontend/src/components/sathi/speech.ts` | live |

---

## 2. For the pharmacist or doctor (reviewer)

| Feature | What it does | Where | Code | Status |
| --- | --- | --- | --- | --- |
| Personal reviewer login | Each reviewer opens a personal invite link; the API stores only a hash of the token and records who made every decision. | `/review?invite=…` | `backend/app/main.py` (`current_reviewer`) | live |
| Review queue | Ordered by an explainable household risk score: open findings, age, number of medicines and prescribers, anticholinergic burden, low adherence, missed check-ins. Every point shows its reason. | `/review` | `backend/app/triage.py` | live |
| Evidence side by side | The strip photos, brands, generics, the rule that fired and its source; confirm or dismiss with a note; undo. Keys: J/K move, C confirm, D dismiss, N note. | `/review` | `frontend/src/app/(review)/review` | live |
| "Why?" graph path | For each finding, the knowledge-graph path that explains it (e.g. Osartil Plus → losartan → ARB → raas group), each step with its source table. | `/review` | `backend/app/medgraph.py`, `GET /flags/{id}/why` | live |
| AI case summary (Graph RAG) | A short facts-only summary built only from numbered graph facts and the findings. Every sentence must cite one; uncited sentences, advice, doses or unknown names drop it. Older version as fallback; starts collapsed after 10 reviews. | `/review` | `backend/app/clinical.py`, `prompts/case_summary.v2.md` | live with a model |
| Kidney function | Enter a creatinine result; eGFR with the 2021 CKD-EPI equation and the KDIGO stage; kidney-dose rules and a test-due reminder. | `/review` | `backend/app/kidney.py` | live |
| Blood-pressure trend | Weekly change in systolic pressure with a 95% confidence interval (reviewer only). | `/review` | `backend/app/stats.py` | live |
| Adherence | 14-day taken rate per medicine with a 95% Wilson interval, and how many expected doses were recorded at all. | `/review` | `backend/app/main.py` (`adherence_summary`) | live |
| Check-in history | Recent calls and WhatsApp check-ins with the answer rate. | `/review` | `backend/app/voice_calls/service.py` | live |
| Clinical notes | What each medicine is for, mark stopped, approve the times of day, confirm allergies, answer the family's questions, approve Ramadan plans. | `/review` | — | live |
| Pack observations | A reviewer-only checklist for pack and seller notes; the app never calls a medicine fake. | `/review` | — | live |

## 3. For the team (admin)

| Feature | What it does | Where | Status |
| --- | --- | --- | --- |
| Reviewer invites | Create, revoke and re-issue personal reviewer invite links. | `/admin` (admin token) | live |
| Lost family link | Re-issue a household's private link. | `/admin` | live |
| Emails | "Results ready" once a batch is reviewed, and the weekly report, for families who opted in (Resend); never notes or the family key. | automatic, `POST /admin/notify/weekly` | live with a key |
| Scheduled jobs | GitHub Actions: weekly email, keep-alive pings, and the check-in cron (off until a provider is live). | `.github/workflows/` | live |
| n8n automations | Doctor alert on red flags and emergencies (ids only), weekly report, refill reminder. | `automations/` | ready |

## 4. Safety rules (the engine)

All of these are deterministic Python with tests; none uses a language model. Sources are in the code and in each data row.

- **Duplicates:** the same generic twice (combination tablets are checked ingredient by ingredient, and registered salt names are reduced to the base generic, so Zimax and Azithrocin are both azithromycin) and two medicines of the same class.
- **Drug interactions:** including the hypertension and diabetes pairs (a beta-blocker with a sulfonylurea, a steroid with metformin).
- **AGS Beers Criteria for 65+.**
- **Expired and expiring strips.**
- **Anticholinergic burden:** Anticholinergic Cognitive Burden scale total of 3 or more at 65+.
- **Look-alike / sound-alike brand names:** Jaro-Winkler similarity plus a phonetic key.
- **Triple whammy:** an ACE inhibitor or ARB with a diuretic and an NSAID.
- **Kidney dose and kidney test due:** metformin thresholds.
- **WHO AWaRe antibiotics:** a Watch antibiotic from a drug shop, or any Reserve antibiotic, goes to a clinician.
- **STOPP/START v3:** ready for criteria the pharmacist enters.

Code: [`backend/app/rules.py`](../backend/app/rules.py); tables: [`backend/data/`](../backend/data).

## 5. For judges and visitors

| Feature | Where | Status |
| --- | --- | --- |
| Landing page with the live strip demo, sourced problem numbers, FAQ and team | `/` | live |
| Keyboard-paced walkthrough of the whole product | `/demo` | live |
| Invented demo household (Rahima Begum, 68, Cumilla), reset in about a second | `/p/1`, demo bar | live |
| Technical docs with live numbers (tests, evals, retrieval, review time, pilot) | `/docs` | live |
| AI models in use, with a picker to put a preferred model first | `/models` | live |
| Design system | `/styleguide` | live |
| Check-in call simulator | `/call-demo` | simulator |
| Privacy, terms, contact, join as a pharmacist | `/privacy`, `/terms`, `/contact`, `/for-pharmacists` | live |

## 6. For developers

| Feature | Where |
| --- | --- |
| MCP server with four read-only tools (`match_brand`, `lookup_unknown_brand`, `check_medicines`, `explain_flag_path`) | [`mcp/`](../mcp) |
| Evaluations: strip reading, Sathi safety, guide retrieval, case summary, BP photos, intent model, missed-dose model | [`eval/`](../eval), [`eval/README.md`](../eval/README.md) |
| Photo labelling tool (local browser page, privacy checklist) | `backend/scripts/label_photos.py` |
| Scripts: seed the demo, index the guide, import brands / DDInter / AWaRe, generate call audio, submit the WhatsApp template, generate these docs | [`backend/scripts/`](../backend/scripts) |
| Versioned prompts (a change means a new file and a new eval run) | [`backend/app/prompts/`](../backend/app/prompts) |
| Deployment (Render, Supabase, Vercel) | [`DEPLOY.md`](DEPLOY.md) |
