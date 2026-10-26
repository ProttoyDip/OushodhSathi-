# OushodhSathi — DESIGN.md

> Source of truth for every UI change. Copied from the DESIGN BRIEF in BUILD_PLAN.md.


## The idea behind the look
**"The pharmacist's ledger."** Calm, warm, trustworthy, unmistakably Bangladeshi, and
built for a 68-year-old's daughter reading on a cheap Android phone. It must look like a
real health product a hospital would trust, not a hackathon AI demo.

Visual metaphor: **prescription paper and medicine-strip foil.**
- Background: warm paper `#F6F2E9` (light) / deep ink `#0F1E22` (dark).
- Primary ink: deep teal-ink `#12343B`. Primary action: teal `#0F6B6B`.
- Foil accent: cool silver `#C9CED3` for strip cards and dividers (subtle, never shiny).
- Severity — always colour **+ icon + word**, never colour alone:
  - Red `#B42318` = confirmed danger / doctor review ("ডাক্তার দেখবেন")
  - Amber `#B54708` = pharmacist review ("ফার্মাসিস্ট দেখবেন")
  - Green `#067647` = checked, no problem found (use sparingly)
- Define all colours as CSS variables / Tailwind tokens, with a proper dark theme.

## Typography
- Bangla body: **Hind Siliguri** (fallback Noto Sans Bengali).
- Bangla display: **Tiro Bangla** (warm serif, used for headings and the passport).
- Latin body: **Instrument Sans**. Latin display: **Instrument Serif**.
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
5. **MedicinePassport** — an A5/A6 printable card: Tiro Bangla title, patient's medicines
   grouped by time of day (সকাল / দুপুর / রাত), generic names large, brand small,
   doctor-confirmed notes, QR code, "Show this at every doctor visit".
6. **BPTrend** (Recharts) — 7-day line with the 140/90 target as a labelled reference line.

## Motion
Only meaningful motion: cards assembling after a scan, the duplicate snap, a confirmed
flag settling into place. 150–250ms, ease-out. Respect prefers-reduced-motion.

## ANTI-SLOP CHECKLIST — reject the screen if any of these appear
- Purple/blue gradients, glassmorphism, neon glow, 3D blobs, mesh backgrounds.
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
