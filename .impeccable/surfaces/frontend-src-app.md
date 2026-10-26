---
version: 1
slug: "frontend-src-app"
primary_target: "frontend/src/app"
related_targets: []
---

Scope: OushodhSathi web frontend (family app = Operate, mobile-first Bangla; reviewer dashboard = Operate, desktop; passport = print artifact; landing = Persuade; /docs = Read).
Audience/job: see PRODUCT.md. Constraints: DESIGN.md is binding (brief-pinned world).

## Direction contract
THESIS: The medicine strip is the interface. Every medicine is drawn as a piece of foil blister strip lying on prescription paper, and every finding is a physical join between strips (the red bracket). Refuses the health-app default of stat tiles, chat bubbles and gradient heroes.
OWN-WORLD: Warm paper ground #F6F2E9 (dark: deep ink #0F1E22); teal-ink #12343B text; teal #0F6B6B for the one action; foil silver #C9CED3 strip edges with perforation notches and blister domes; severity red #B42318 / amber #B54708 / green #067647 always as icon + word + colour. Tiro Bangla + Instrument Serif display, Hind Siliguri + Instrument Sans body, tabular numerals. 8px cards, 999px chips, one soft offset shadow.
STORY: The family sees the whole shelf as one list, learns a clinician checked it, and knows what to carry to the next visit. The reviewer decides each finding in under 30 seconds.
FIRST VIEWPORT: Family home at 390px: wordmark + language toggle; the patient as a prescription header (name in Tiro Bangla, age, last checked); one full-width teal action "ওষুধ স্ক্যান করুন" in thumb reach; below, the confirmed-results line and passport link. Reviewer at 1440px: queue column (ReviewRows, red first) left, evidence centre (StripCards side by side joined by the connector, rule, source), patient sidebar right, actions with C/D/N/J/K hints.
SIGNATURE: DuplicateConnector snap — two StripCards slide together (220ms ease-out) and a red bracket draws itself labelled "দুটোই প্যারাসিটামল". Motion grammar: assemble, snap, settle; nothing else moves.
FORM: brief-pinned by DESIGN.md; no concept-seed roll; seed key: none (pinned).
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
