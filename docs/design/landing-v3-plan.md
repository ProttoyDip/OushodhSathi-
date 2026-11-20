# Landing v3 — "The medicine shelf, sorted"

Plan for Prompt 15 (phase 15A). No code yet. Binding inputs: `DESIGN.md` (Neel, anti-slop checklist, motion rules),
`AGENTS.md`, `PRODUCT.md`, `docs/FEATURES.md`. Branch: `design/landing-v3` (from `main` at `f3f1c94`).

## 0. What the current page does (measured on 20 Nov, local build of `main`)

| Review point | Verdict | Evidence |
| --- | --- | --- |
| 1. First screen mostly empty | **True** | At first paint the hero's right half is empty and the headline is mid-fade; 28 of 34 `[data-reveal]` blocks had opacity 0. On a 390 px phone no product is visible above the fold at all. |
| 2. Blank while scrolling | **True** | A fast jump to 45% of the page shows one column of text and an empty right half. |
| 3. One tone in dark mode | **True** | Every section is `--paper` / `--paper-raised` (#0a0e1c / #11172c), which are nearly identical. |
| 4. The best moment is hidden | **Partly** | On desktop the real Napa + Ace + bracket already appear in the hero, but only after the entry animation, and on phones below the fold. |
| 5. Marquee small and grey | **True** | 17 px brand names, a 17 px grey title, no link between the pairs. |

The diagnosis in the prompt is right. The cause is mechanical, not visual taste: content is gated behind
scroll triggers and an entry animation, so the page is empty whenever the camera moves.

## 1. Design plan

**Concept.** *The medicine shelf, sorted.* A calm pharmacist puts a messy shelf in order. The one memorable
thing: two strips with different names slide together and a kantha-stitched bracket says they are the same
medicine, and then a pharmacist's check lands. Everything else on the page supports that one beat.

**Palette** (all existing `DESIGN.md` tokens; no new colour):

| Name | Token | Hex (light) | Role |
| --- | --- | --- | --- |
| Porcelain | `--paper` | `#F3F5F9` | page ground, light by default on the landing page |
| Ink | `--ink` | `#0E1530` | text |
| Neel dye | `--neel` / `--dye` | `#2A3B91` / `#1F2C6E` | primary action; the one dyed band |
| Foil | `--foil` | `#C8CDD6` | strip edges, marquee chips |
| Stitch | `--stitch` | `#8F9BD6` | the kantha running stitch |
| Finding red | `--red` | `#B42318` | **only** the confirmed-finding bracket and badge (colour + icon + word) |

**Type roles.** Display: Anek Bangla 500 (bn) / Schibsted Grotesk 600, −0.035em (en). Body: Hind Siliguri / Instrument
Sans, ≥ 18 px, Bangla line-height ≥ 1.6. Numbers: tabular figures. No italic display, no eyebrows.

### Principles

1. **Visible first, moving second.** The server renders every section complete. Motion changes *state* of things
   already on screen (apart → together, waiting → confirmed); it never makes hidden things appear.
2. **One story beat, told three times.** Hero (the moment), marquee (why it happens), story section (how we
   catch it). Everything else is calm and dense.
3. **Real components, real numbers.** StripCard, SeverityBadge, DuplicateConnector from the product; counts
   and results generated from `backend/data` and `eval/` files into committed JSON, checked by a test.
4. **Rhythm through surfaces, not effects.** Porcelain → white → *one deep-indigo dyed band* → white →
   porcelain. In dark mode the band stays the strongest surface so the rhythm survives.
5. **Motion is opt-out everywhere.** Reduced motion, the site-wide Pause motion toggle and JavaScript-off
   all show the same complete final state.

## 2. Page structure

| # | Section | Surface | Motion | Notes |
| --- | --- | --- | --- | --- |
| 1 | Hero | porcelain | **the** orchestrated sequence (≤ 2.4 s, once per visit, replay) | real StripCards; final state server-rendered |
| 2 | Problem marquee | white, full width | two rows, opposite directions; pause button + site toggle | larger foil chips; pairs share a stitched underline; caption counts from data |
| 3 | How it works | porcelain | the one scroll-linked section (desktop only) | sticky phone + five steps; mobile = plain list with inline visuals |
| 4 | Rules band | **dyed indigo, kantha hem** | none | the rule families, each with its source |
| 5 | For pharmacists | white | none | 2× reviewer screenshot + three callouts |
| 6 | Daily follow-up | porcelain | none | WhatsApp message + call keypad previews, "simulator" note |
| 7 | Evidence, honestly | white | none | numbers from results JSON with n and 95% CI, kinds labelled |
| 8 | Team · FAQ · final CTA · footer | porcelain / white | none | existing content, tighter spacing |

### What I removed, and why

| Removed | Why |
| --- | --- |
| `reveal()` / `[data-reveal]` scroll reveals on the landing page | They hide content until a trigger fires: the cause of review points 1 and 2. |
| Headline `line-rise` and the hero entry fade | First paint must already show the claim and the product. |
| Stitches that "sew in" on scroll (except inside the hero bracket) | Decoration that hides a divider until scroll; keeps motion to the three allowed places. |
| The six "how it works" cards (`HowTimeline`) | Replaced by the story section, which shows each step with real components. |
| The two-column safety list (r1, r3–r6) | Folded into the story steps (step 5 is the r2 promise), the rules band, and the FAQ; the "Read the safety design" link stays. |
| The small grey marquee title | The marquee becomes the problem statement with its own heading and a data caption. |

## 3. Wireframes

### Desktop (1440 × 900, first screen)

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ ওষুধসাথী     কীভাবে · নিয়ম · ফার্মাসিস্ট · প্রশ্ন · ডকস    [Ⅱ গতি থামান] [◐] [English]      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  নাপা আর এস —                         ┌─ dyed cloth, kantha hem ───────────────────┐   │
│  একই ওষুধ।            (display 76px)   │  রহিমা বেগমের তাক               ↻ replay  │   │
│  Different names, same medicine.        │  ┌─────────────────────────────┐          │   │
│                                         │ ┃│ Napa 500 mg · প্যারাসিটামল  │          │   │
│  One sentence: photos → one checked     │ ┃│ Local drug shop      ▓▓▓▓▓ 96%│          │   │
│  list, a pharmacist confirms first.     │ ┃├── ⛓ দুটোই প্যারাসিটামল ─────┤  (red,  │   │
│                                         │ ┃│ Ace 500 mg · প্যারাসিটামল   │   icon + │   │
│  [ ডেমো দেখুন → ]  [ পরিবারের তালিকা ]  │ ┃│ Village doctor       ▓▓▓▓▓ 98%│   word)  │   │
│  Demo household note · ▶ demo video     │  └─────────────────────────────┘          │   │
│  ───────────────────────────────        │  Camlodin 5 mg · অ্যামলোডিপিন            │   │
│  ✓ pharmacist confirms every finding    │  ✓ ফার্মাসিস্ট নিশ্চিত করেছেন  (green)    │   │
│  ✓ Bangla first   ✓ photos not stored   │  Demo household — invented data           │   │
│                                         └───────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Mobile (390 × 844, first screen)

The product moves **above** the body text so a phone sees the moment without scrolling.

```text
┌──────────────────────────────┐
│ ওষুধসাথী        [Ⅱ] [◐] [En] │
├──────────────────────────────┤
│ নাপা আর এস —                  │
│ একই ওষুধ।                     │
│ Different names, same medicine│
│ ┌ compact pair (no cloth) ─┐  │
│ ┃ Napa 500 mg              │  │
│ ┣─ ⛓ দুটোই প্যারাসিটামল ──┤  │
│ ┃ Ace 500 mg               │  │
│ └──────────────────────────┘  │
│ ✓ ফার্মাসিস্ট নিশ্চিত করেছেন   │
│ [      ডেমো দেখুন →        ]  │
│ [  পরিবারের তালিকা বানান   ]  │
│ (body sentence, trust lines   │
│  below the fold)              │
└──────────────────────────────┘
```

### Sections 2–8 (desktop; mobile stacks every row into one column)

```text
2 MARQUEE (white, full bleed)
  একটি ওষুধ, অনেক নাম                                            [Ⅱ থামান]
  ◀ [▌Napa → প্যারাসিটামল] [▌Camlodin → অ্যামলোডিপিন] [▌Ace → প্যারাসিটামল] ...   (row 1, ~60s)
    [▌Maxpro → ইসোমিপ্রাজল] [▌Osartil → লোসারটান] [▌Sergel → ইসোমিপ্রাজল] ... ▶ (row 2, opposite)
  pairs share a stitched underline in the same position; hover/focus a chip → its row pauses, its pair lights
  caption: "আমাদের ব্র্যান্ড তালিকায় ৩০টি নাম, ২৬টি জেনেরিক: ৪টি জেনেরিক একাধিক নামে বিক্রি হয়" (from data)

3 HOW IT WORKS (porcelain)  — desktop: sticky phone left, steps right; mobile: list with inline visuals
  ┌ phone (sticky) ┐   ① ছবি তুলুন      Family photographs every strip, box, prescription
  │ step visual    │   ② পড়া            AI reads brand, strength, expiry, confidence
  │ changes with   │   ③ মেলানো          Brand → generic (exact, then strict fuzzy; Bangla names)
  │ scroll         │   ④ নিয়ম           The rules engine — no AI — finds the duplicate, with its source
  └────────────────┘   ⑤ নিশ্চিত          A pharmacist or doctor confirms before the family sees it

4 RULES BAND (deep indigo dyed cloth, kantha hem)
  যে নিরাপত্তা নিয়মগুলো চলে        "Deterministic rules, every one with its source. No AI decides."
  ⧉ same medicine twice — brand table      ⇄ two drugs, same class — class table
  ⚠ known interactions — curated table*     65+ AGS Beers Criteria — AGS 2023
  ⊙ anticholinergic burden — ACB scale      Aa look-alike names — Jaro-Winkler + phonetic key
  ⚕ triple whammy — Medsafe NZ 2013        ⌁ kidney dose — CKD-EPI 2021, FDA 2016
  ℞ antibiotics — WHO AWaRe 2025           ⌛ expiry — printed date
  * "pharmacist review pending" shown as written in the data, not hidden

5 FOR PHARMACISTS (white)
  [ large 2× reviewer queue screenshot, light, hairline frame ]   1 Risk-ordered queue (every point has a reason)
                                                                  2 "Why?" — the knowledge-graph path, with sources
                                                                  3 J / K / C / D — decide in under 30 seconds

6 DAILY FOLLOW-UP (porcelain)
  [ WhatsApp message with 3 buttons ]   [ call keypad 1 · 2 · 9 ]
  "Simulator — connecting a phone provider and a WhatsApp Business number is next."  → try each

7 EVIDENCE, HONESTLY (white)
  Real photos: "evaluation in progress (n = 0 labelled)" until ≥ 25
  Sathi safety 33/33 medical · 10/10 emergency · retrieval 95% (95% CI 88–98%)
  Synthetic benchmark (computer-drawn) — brand 40/45, 95% CI 76–95%; BP screens 20/20      → /docs
  public problem numbers with sources (existing three)

8 TEAM · FAQ · final CTA · footer (existing content; tighter spacing)
```

## 4. Motion storyboard

### Hero (≤ 2.4 s, once per visit; `sessionStorage` remembers; replay button reruns it)

The server renders the **final** state. Before first paint, the existing inline head script (the same pattern
as `revealArmScript`) adds `html.motion-ok` only when motion is allowed (no reduced motion, toggle not paused).
Only under that class do the start-state transforms apply, so there is no flash and no hidden content. Every
change is `transform` or a colour change: no layout shift.

| Time | Frame |
| --- | --- |
| 0.0 s | First paint, start state (only with `motion-ok`): Napa and Ace both fully visible, Ace laid down askew (16 px right, 6 px lower, tilted 1.5°; built first as 28 px lower, which overlapped Camlodin); the pair label reads in neutral ink "দুটোই প্যারাসিটামল?"; status row reads "ফার্মাসিস্টের অপেক্ষায়". |
| 0.3–0.9 s | Ace settles beside Napa (a CSS spring-like curve, so the hero ships no motion library); Camlodin keeps its place (it was already in its final position). |
| 0.9–1.4 s | The red kantha bracket draws in from the middle outwards (the existing `reveal-y` keyframe in `DuplicateConnector`). |
| 1.4–1.7 s | The label becomes the red SeverityBadge: icon + "দুটোই প্যারাসিটামল" (the question mark goes). |
| 1.7–2.4 s | The status row's waiting dot becomes a green check and the words change to "ফার্মাসিস্ট নিশ্চিত করেছেন". |
| after | Rest. The replay button rewinds to the start state and plays again. |

Without JavaScript, with reduced motion, or with Pause motion on: the 2.4 s frame from the first paint.

### How it works (desktop ≥ 1024 px only)

`useScroll({ target })` over the five steps; `useTransform` maps progress to a step index (0–4). The phone
frame is `position: sticky`. Each step's text is always readable; the phone visual is an illustration of
the active step and crossfades between steps (opacity on overlaid layers, 180 ms).

| Progress | Phone shows | Text highlighted |
| --- | --- | --- |
| 0–20% | a strip photo with the scan stitch frame | ① ছবি তুলুন |
| 20–40% | three StripCards with confidence bars (one dashed: "যাচাই করুন") | ② পড়া |
| 40–60% | brand → generic chips (Napa → প্যারাসিটামল, Ace → প্যারাসিটামল) | ③ মেলানো |
| 60–80% | the finding: rule name, evidence line, data source | ④ নিয়ম |
| 80–100% | the reviewer's confirm with a note, then the family view | ⑤ নিশ্চিত |

Below 1024 px, without JavaScript, or with motion paused: an unpinned list, each step with its own static
visual inline.

### Marquee

Two CSS-only rows (≈ 60 s and 75 s per loop, opposite directions). Hovering or focusing a chip pauses its row
and gives its pair a stronger stitched underline. A visible "থামান / চালান" button and the site toggle stop both
rows. Screen readers get one sentence instead of the moving list.

## 5. Copy (Bangla first)

| Section | Bangla | English |
| --- | --- | --- |
| Hero h1 | নাপা আর এস — একই ওষুধ। | Napa and Ace are the same medicine. |
| Hero line | নাম আলাদা, ওষুধ একই। আমরা পুরো তাকটা একসাথে দেখি। | Different names, one medicine. We look at the whole shelf at once. |
| Hero body | ঘরের প্রতিটি ওষুধের ছবি তুলুন। ওষুধসাথী একই ওষুধ দুইবার, ঝুঁকিপূর্ণ মিশ্রণ আর মেয়াদোত্তীর্ণ পাতা খুঁজে বের করে; পরিবার দেখার আগে একজন ফার্মাসিস্ট বা ডাক্তার নিশ্চিত করেন। | Photograph every medicine in the house. OushodhSathi finds the same medicine twice, risky combinations and expired strips, and a pharmacist or doctor confirms before the family sees anything. |
| CTAs | ডেমো দেখুন · পরিবারের তালিকা বানান | See the demo · Start for your family |
| Hero states | দুটোই প্যারাসিটামল? → দুটোই প্যারাসিটামল · ফার্মাসিস্টের অপেক্ষায় → ফার্মাসিস্ট নিশ্চিত করেছেন | Both paracetamol? → Both paracetamol · Waiting for the pharmacist → Confirmed by a pharmacist |
| Motion toggle | গতি থামান · গতি চালু করুন | Pause motion · Play motion |
| Marquee h2 | একটি ওষুধ, অনেক নাম | One medicine, many names |
| Marquee caption | আমাদের ব্র্যান্ড তালিকায় {brands}টি নাম, {generics}টি জেনেরিক — {shared}টি জেনেরিক একাধিক নামে বিক্রি হয়। | Our brand table: {brands} names, {generics} generics — {shared} generics sold under more than one name. |
| Marquee (screen reader) | উদাহরণ: নাপা আর এস দুটোই প্যারাসিটামল; ক্যামলোডিন আর অ্যামডোকাল দুটোই অ্যামলোডিপিন। | For example: Napa and Ace are both paracetamol; Camlodin and Amdocal are both amlodipine. |
| How h2 | কীভাবে কাজ করে | How it works |
| Steps | ছবি তুলুন · পড়া · মেলানো · নিয়ম · নিশ্চিত | Photograph · Read · Match · Rules · Confirm |
| Step 4 line | নিয়ম-ইঞ্জিন (এআই নয়) সমস্যা খুঁজে পায়, সূত্রসহ। | The rules engine — not AI — finds the problem, with its source. |
| Step 5 line | পরিবার দেখার আগে ফার্মাসিস্ট বা ডাক্তার নিশ্চিত করেন। | A pharmacist or doctor confirms before the family sees it. |
| Rules h2 | যে নিরাপত্তা নিয়মগুলো চলে | The safety rules that run |
| Rules line | নির্দিষ্ট নিয়ম, প্রতিটির সূত্রসহ। কোনো এআই সিদ্ধান্ত নেয় না। | Fixed rules, each with its source. No AI decides. |
| Pharmacists h2 | ফার্মাসিস্টের জন্য: ৩০ সেকেন্ডে সিদ্ধান্ত | For pharmacists: decide in 30 seconds |
| Follow-up h2 | প্রতিদিনের খোঁজ, ফোনে বা হোয়াটসঅ্যাপে | A daily check-in, by call or WhatsApp |
| Follow-up note | এখন সিমুলেটর — ফোন সেবা আর হোয়াটসঅ্যাপ বিজনেস নম্বর যুক্ত করা পরের ধাপ। | Simulator for now — connecting a phone provider and a WhatsApp Business number is next. |
| Evidence h2 | প্রমাণ, সৎভাবে | Evidence, honestly |
| Evidence kinds | আসল ছবি · কৃত্রিম বেঞ্চমার্ক (কম্পিউটারে আঁকা ছবি) | Real photos · Synthetic benchmark (computer-drawn images) |

Existing FAQ, team, CTA and footer copy stays. Rule names and sources reuse the reviewer's existing rule labels.

## 6. Engineering notes for 15B–15F

- **Static-first.** No landing element starts at `opacity: 0`. The landing stops using `reveal()`. A JS-off
  check in 15F asserts every section's text is in the server HTML.
- **Motion gate.** One inline head script sets `html.motion-ok` when motion is allowed; `usePauseMotion()` reads and
  writes the toggle (`localStorage`, wrapped in try/catch) and flips the same class live.
- **Data, not typed numbers.** `frontend/src/data/brandFacts.json` (from `backend/data/brands_seed.csv`) and
  `frontend/src/data/evidence.json` (from `eval/**/results*.json`), written by a generator script and committed;
  a backend test fails if either is out of date. Vercel builds only `frontend/`, so the page must not read
  `../backend` or `../eval` at build time.
- **Budgets.** No new dependency (`motion` is already in the bundle); added landing JS < 40 KB gzipped;
  product images WebP < 200 KB with width and height; LCP < 2.5 s, CLS < 0.1 on Lighthouse mobile.

## 7. Self-review against Prompt 15 and DESIGN.md

| Check | Result |
| --- | --- |
| Stays in Neel; no new accent | Pass: six existing tokens; red only on the confirmed finding. |
| Anti-slop checklist | Pass: no gradients, glow, glass, sparkle icons, stock photos, fake numbers or logo walls. The cloth's existing faint texture stays as it is in DESIGN.md. |
| Content visible without animation | Pass: final state server-rendered; start states only under `motion-ok`. |
| Motion only in three places | Pass: hero sequence, story section, marquee. |
| WCAG 2.2.2 | Pass: marquee pause button, site-wide toggle, reduced motion = static final state. |
| Every number real | Pass: counts and results from generated JSON with a test; "pilot not started" and "evaluation in progress" stay. |
| Bangla first, line-height ≥ 1.6, targets ≥ 48 px | Pass in plan; verified with screenshots in each phase. |

### Revisions after review

1. *First draft hid the "both paracetamol" label until the strips met.* That is hidden content. Revised: the label is
   always present and changes state (question → finding), and the status row changes words rather than appearing.
2. *First draft read counts and results from `../backend` and `../eval` at build time.* Vercel builds only
   `frontend/`. Revised: generated, committed JSON with a test.
3. *First draft kept the cloth panel on mobile.* It pushed the pair below the fold. Revised: a compact pair without
   the cloth sits above the body text on phones.

## 8. Decisions for you

1. **Light by default on the landing page.** The prompt asks for it. My proposal: when the theme setting is
   "system", the landing page uses light even if the phone is in dark mode; an explicit dark choice in the toggle is
   always honoured. The rest of the app keeps following the system setting. OK?
2. **The six safety promises.** They move into the story steps, the rules band and the FAQ instead of their own
   section. OK, or keep a short promises list?
3. **21st.dev and Figma.** I skipped the 21st.dev inspiration search for the plan (it uses credits, and you asked
   earlier to cut its usage); I can run one search for the marquee and the sticky story in 15C. Figma frames are
   optional; say if you want them.
