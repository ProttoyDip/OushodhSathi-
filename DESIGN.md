# OushodhSathi — DESIGN.md

> Source of truth for every UI change. Started from the DESIGN BRIEF in BUILD_PLAN.md;
> the visual identity was revised to "Neel" (indigo) in October 2026.


## The idea behind the look
**"Neel" (নীল) — Bengal indigo, medicine foil and the kantha stitch.** Calm, clinical,
trustworthy and unmistakably Bangladeshi, built for a 68-year-old's daughter reading on a
cheap Android phone. It must look like a real health product a hospital would trust, not a
hackathon AI demo and not a generic SaaS template.

Why indigo: Bengal's indigo dye (নীল) is local heritage, and blue is the one hue that never
competes with the red / amber / green severity colours. Warm beige paper and editorial serifs
are deliberately avoided.

Materials:
- Canvas: cool porcelain `#F3F5F9` (light) / indigo night `#0A0E1C` (dark). Cards are white / `#11172C`.
- Ink: deep indigo-black `#0E1530`. Primary action: indigo dye `#2A3B91` (dark: `#98A8F6`).
- Foil accent: cool silver `#C8CDD6` for strip cards and the flow strip (subtle, never shiny).
- **Kantha stitch** (`--stitch`): the dashed running stitch of Bengali quilts. Used sparingly:
  section underlines, the scan frame, completed progress, the stitched hem of the one
  indigo-dyed cloth panel (`.dyed-cloth`) that holds a page's hero object.
- Severity — always colour **+ icon + word**, never colour alone, and reserved for findings:
  - Red `#B42318` = confirmed danger / doctor review ("ডাক্তার দেখবেন")
  - Amber `#B54708` = pharmacist review ("ফার্মাসিস্ট দেখবেন")
  - Green `#067647` = checked, no problem found (use sparingly)
- All colours are CSS variables / Tailwind tokens in `frontend/src/app/globals.css`, with a
  full dark theme. Every text pair passes WCAG AA; body text is ≥ 7:1.

## Typography
- Bangla body: **Hind Siliguri** (fallback Noto Sans Bengali).
- Bangla display: **Anek Bangla** (variable, weight 500 for headings and the passport).
- Latin body: **Instrument Sans**. Latin display: **Schibsted Grotesk** (variable, weight 600,
  tracking −0.035em) — a sturdy newspaper grotesk, set tight but never shouting.
- Family app body text minimum **18px**, line-height 1.6 for Bangla (Bangla needs room).
- Numbers (strengths, BP readings) use tabular figures.

## Rules for the family app (elder-friendly)
- Bangla first, English toggle. Every string in a locale file so a native speaker can fix it.
- One primary action per screen. Touch targets ≥ 48px. Body contrast ≥ 7:1 where possible.
- Plain words: "একই ওষুধ দুইবার" not "therapeutic duplication".
- Works on 360px wide screens and slow 3G (no heavy images, no layout shift).

## Rules for the reviewer dashboard (pharmacist/doctor)
- Dense, calm, desktop-first. Keyboard: J/K move, C confirm, D dismiss, N add note.
- Evidence side by side: the two strip photos, brands, generics, the rule that fired,
  and its source. A reviewer should decide in under 30 seconds.

## Signature components (make these beautiful; they carry the demo)
1. **StripCard** — looks like a piece of medicine strip: foil-textured edge, brand in
   bold, generic as a chip, strength, expiry, a small confidence bar, the photo crop.
   Low confidence = dashed border + "যাচাই করুন" (please check).
2. **DuplicateConnector** — when two StripCards share a generic, they slide together
   and a red bracket joins them with the label "দুটোই প্যারাসিটামল" (both are
   paracetamol). This is the hero moment of the video.
3. **SeverityBadge** — icon + word + colour, three sizes.
4. **ReviewRow** — queue row with severity, patient age, rule, time waiting.
5. **MedicinePassport** — an A5/A6 printable card: Anek Bangla title, patient's medicines
   grouped by time of day (সকাল / দুপুর / রাত), generic names large, brand small,
   doctor-confirmed notes, QR code, "Show this at every doctor visit".
6. **BPTrend** (Recharts) — 7-day line with the 140/90 target as a labelled reference line.

## Motion
Motion explains, it never decorates. One spring for the product (`SPRING` in
`components/Motion.tsx`, stiffness 420 / damping 38) and a slower one for large travel.
- **Cards keep their identity**: a strip that appears in two states (pile → list → duplicate
  pair → review) shares a `layoutId` and travels between them instead of popping.
- The duplicate bracket reveals from the middle outwards after the pair lands.
- Panels enter with a short rise (24–28px) and settle; captions crossfade.
- Buttons answer a press (scale 0.97); linked cards lift 2px on hover.
- `MotionConfig reducedMotion="user"` and the CSS reduced-motion rule turn all of it off.

## ANTI-SLOP CHECKLIST — reject the screen if any of these appear
- Purple/blue gradients, glassmorphism, neon glow, 3D blobs, mesh backgrounds.
  (Indigo is a flat dye colour here, never a gradient or a glow.)
- Sparkle "AI" icons, robot mascots, "AI-powered" badges, emoji as icons.
- Generic hero copy ("Revolutionizing healthcare with AI").
- A grid of identical stat cards with fake numbers. Any fake testimonial or logo wall.
- Lorem ipsum, placeholder avatars, stock photos of smiling doctors.
- Inconsistent icon sets, random border radii, more than one accent colour per screen.
- Text over busy images; grey-on-grey low contrast; tiny 12px body text.
- Default shadcn look with no tokens applied.
- Any number on screen that is not real data or clearly labelled demo data.

## Design QA loop (do this for EVERY screen)
1. Build it with the frontend-design skill (if available) and DESIGN.md tokens.
2. Screenshot it with the Playwright/browser MCP at **390×844** and **1440×900**, light and dark.
3. Review the screenshots against this brief and the anti-slop checklist. List problems.
4. Fix and re-screenshot until a demanding product designer would ship it.
5. Save final screenshots to /docs/screens/.
