# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Family member (primary payer and reader).** Often a daughter or son living in another
  city or abroad (demo: Nusrat in Toronto) caring for a parent aged 65+ in Bangladesh with
  hypertension and/or type 2 diabetes. Reads on a cheap Android phone, in Bangla first.
  Job: photograph every medicine in the house, confirm the list, and understand what a
  clinician found — without medical jargon.
- **Reviewer (pharmacist or doctor).** Works at a desktop through a queue of findings.
  Job: confirm or dismiss each rule finding in under 30 seconds, with a note.
- **The patient.** Carries the printed medicine passport to every doctor visit.
- **Judges** of the International AI Builders Congress 2026 (HealthSphere AI → ChronicCare AI)
  evaluate the landing page, /docs module, live demo and video.

## Product Purpose

Elderly Bangladeshis collect medicines from a hospital doctor, a village doctor and the
local drug shop, under tens of thousands of brand names. Nobody looks at the whole shelf.
OushodhSathi turns photos of every strip, box and prescription into one structured,
clinician-checked list, catches duplicates, interactions, drugs risky after 65 and
expired strips, and gives the family a plain-Bangla explanation, a weekly report and a
printable medicine passport. Success: a dangerous duplicate (e.g. Napa + Ace, both
paracetamol) is caught, confirmed by a clinician, and understood by the family.

## Positioning

**AI for perception, rules and humans for judgement.** A vision model only reads photos;
a deterministic rules engine creates every finding; a pharmacist or doctor confirms every
finding before the family sees it. The app never tells a patient to stop, start or change
a medicine.

## Operating Context

Family flow: home → scan photos → confirm list (StripCards) → send for checking → status
(under review) → confirmed results → weekly report → medicine passport (print, QR).
Reviewer flow: token login → queue (red first) → evidence side by side → confirm/dismiss
with note, keyboard driven (J/K/C/D/N), undo for 5 seconds.

## Capabilities and Constraints

- Stack (existing codebase): Next.js App Router + TypeScript + Tailwind in /frontend;
  FastAPI in /backend with SQLite locally and Supabase Postgres when deployed (DATABASE_URL);
  next-intl (bn default, en).
- Families see ONLY confirmed flags — enforced by the API.
- Full uploaded photos (strips, boxes and prescriptions, including any prescription header with the patient's name) are processed in memory and discarded after extraction; nothing is stored on the server. For visual strip verification only, a photo of strips or boxes gets a small downscaled thumbnail, returned once and kept only in the family's browser. A photo with a prescription in it gets no thumbnail.
- Low-confidence (< 0.75) and web-found matches always show as needing confirmation.
- Demo mode works with no API keys (returns the demo household).

## Brand Commitments

- Name: OushodhSathi / ওষুধসাথী. Bangla first, English toggle; every string in a locale file.
- Visual direction is fixed in DESIGN.md and is binding: **"Neel"** — Bengal indigo `#2A3B91` on cool
  porcelain `#F3F5F9`, medicine foil, the kantha running stitch (`--stitch`), Anek Bangla and
  Schibsted Grotesk for display, Hind Siliguri and Instrument Sans for body text.
- Closing line used in the video: "build locally, protect globally."

## Evidence on Hand

- Cited public statistics (verified 2026-10-26):
  - Hypertension is the most common illness in Bangladesh — 78.28 per 1,000 people, BBS
    Health and Morbidity Status Survey (HMSS) 2025, as reported by BSS
    (https://www.bssnews.net/others/337437) and The Daily Star
    (https://www.thedailystar.net/health/disease/news/hypertension-most-common-illness-country-4047686).
  - Only 11% of people with hypertension in Bangladesh had blood pressure controlled
    (<140/90) — cited as background in "Evaluation of the WHO-HEARTS hypertension control
    package in Bangladesh: a quasi-experimental trial", Heart (BMJ), 2024
    (https://heart.bmj.com/content/heartjnl/early/2024/07/16/heartjnl-2024-324253.full.pdf).
  - 69% of geriatric outpatients received five or more medicines — small 2011 study of 35
    patients, "Trends of prescribing for out-door geriatric patients in a private hospital
    of Bangladesh" (https://www.academia.edu/111376182). Always cite with its sample size.
- Demo household (Rahima Begum, 68, Cumilla) — invented, always labelled
  "Demo household — invented data".
- **No real pilot data yet.** Never show pilot results; say "pilot in progress".
- No eval results yet until eval/results_*.json exists; say "evaluation in progress".
- Team names, roles and mentor: not provided — leave clearly marked placeholders.

## Product Principles

1. Judgement belongs to rules and clinicians; AI only perceives.
2. Never instruct the patient to stop, start or change a medicine or dose.
3. Every number shown is real or clearly labelled demo data.
4. Elder- and family-first: plain Bangla words, one action per screen.
5. Privacy by default: no names or phone numbers to any model; no photos stored on the server.

## Accessibility & Inclusion

Family app: Bangla body text ≥ 18px with line-height 1.6, touch targets ≥ 48px, body
contrast ≥ 7:1 where possible, works at 360px wide and on slow 3G, severity never shown by
colour alone (colour + icon + word), respects prefers-reduced-motion. Reviewer dashboard:
fully keyboard operable.
