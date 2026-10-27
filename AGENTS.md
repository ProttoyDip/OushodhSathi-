# AGENTS.md — rules for every coding agent (Claude Code, Codex, Antigravity)

## The product

OushodhSathi is a medicine-safety service for elderly Bangladeshis with high blood
pressure or diabetes who collect medicines from several doctors, village doctors and
drug shops. A family member photographs every medicine strip, box and prescription in
the house. AI reads the photos into a structured list. Each Bangladeshi brand is
mapped to its generic. A **deterministic rules engine** (not the AI) flags:
the same generic under two brands, two drugs from the same class, known interactions,
drugs risky for adults 65+ (AGS Beers Criteria), and expired strips. A pharmacist or
doctor **confirms every flag** before the family sees anything. The family gets a
simple Bangla explanation, a weekly report, and a printable **medicine passport**
(Bangla/English list + QR code) to show at every doctor visit.

Core principle: **AI for perception, rules and humans for judgement.**
The app never tells a patient to stop or change a medicine.

## Folder layout

```
/backend       FastAPI (Python 3.12+), Pydantic, Pydantic-AI, RapidFuzz, httpx, pytest
  app/         main.py (API), rules.py (deterministic engine), brands.py (matching),
               store.py (SQLite), models.py, llm_router.py, agent.py, research.py,
               explain.py, prompts/<name>.v<N>.md
  data/        brand, interaction, Beers and duplicate-class tables (CSV/TXT)
  scripts/     import_brands.py, import_ddinter.py, seed_demo.py
  tests/       pytest suite
/frontend      Next.js (App Router, TypeScript), Tailwind, Recharts, lucide-react, next-intl
/mcp           our own MCP server (read-only tools)
/automations   n8n workflow JSON
/eval          extraction eval set + run_eval.py
/docs          design notes, screenshots, video assets
```

## NON-NEGOTIABLE SAFETY RULES

1. Safety flags come ONLY from the deterministic rules engine in `backend/app/rules.py`.
   LLMs never create, remove or change the severity of a flag.
2. Flags start as `pending_review`. Families can ONLY ever see flags with status
   `confirmed`. This is enforced in the API (`GET /patients/{id}/flags?view=family`),
   not just the UI, and covered by `tests/test_api.py`.
3. No text anywhere tells a patient to stop, start or change a medicine or dose.
4. Low-confidence extractions (< 0.75) and web-found brand matches are always shown
   as needing human confirmation.
5. Never send patient names or phone numbers to any LLM. Only medicine photos and
   medicine names.
6. Photos are processed in memory and NOT stored after extraction.

## Sathi (সাথী), the in-app helper

Sathi does three jobs only: tells the family the next step, answers how-to questions
about the app, and passes medical questions to a human. It is not a medical advisor.

- The next step is chosen by the state machine in `backend/app/next_step.py`. The AI
  may only reword it, and every number and medicine name must match the state.
- App answers come only from `docs/help/help_bn.md` and `help_en.md`. If the guide does
  not answer it, Sathi says it doesn't know and offers human help. It never guesses.
- Every message passes `backend/app/guard.py` BEFORE any model sees it, and every model
  answer passes it AFTER. The guard can only make Sathi safer, never less safe. If the
  intent model fails or is unsure, the question counts as MEDICAL.
- Emergency words get a fixed message and a Call 999 button. No AI is involved.
- The model gets only the state code, the retrieved guide entries, the question (patient
  names removed) and medicine names when needed. Never names, phone numbers or addresses.
- Every refusal and redirect is logged anonymised (kind, language, guide ids; no text).
- Replies to family questions are written by the pharmacist, never by AI.
- `eval/run_sathi_eval.py` runs in CI and fails on any medical or emergency leak.

## Secrets

API keys only in `backend/.env` — never in code, prompts, logs, commits or screenshots.
Keep `backend/.env.example` updated with key NAMES only.

## Workflow

- Run `pytest` in `/backend` and `npm run lint && npm run build` in `/frontend` before
  every commit. Small commits with clear messages.
- DESIGN: every UI change must follow `DESIGN.md`. Screenshot and self-review before
  calling a screen done.
- PROMPTS: LLM prompts live in `backend/app/prompts/<name>.v<N>.md`. Changing a prompt
  means a new version file + re-running `eval/run_eval.py`.
