"use client";

import { Pause, Play } from "lucide-react";
import { useState } from "react";

type Chip = { brand: string; en: string; bn: string; pair?: string };

// Rows from backend/data/brands_seed.csv + generics_bn.csv. Brand names stay Latin, as printed on the strip.
// The four generics sold under two names sit at the same position in both rows; `pair` lets a hovered chip
// light its partner (globals.css, .marquee:has(...)). The rows are aria-hidden: screen readers get `sr`.
const ROW_A: Chip[] = [
  { brand: "Napa", en: "paracetamol", bn: "প্যারাসিটামল", pair: "para" },
  { brand: "Camlodin", en: "amlodipine", bn: "অ্যামলোডিপিন", pair: "amlo" },
  { brand: "Maxpro", en: "esomeprazole", bn: "ইসোমিপ্রাজল", pair: "eso" },
  { brand: "Angilock", en: "losartan", bn: "লোসারটান", pair: "losa" },
  { brand: "Seclo", en: "omeprazole", bn: "ওমিপ্রাজল" },
  { brand: "Comet", en: "metformin", bn: "মেটফরমিন" },
  { brand: "Ecosprin", en: "aspirin", bn: "অ্যাসপিরিন" },
  { brand: "Atova", en: "atorvastatin", bn: "অ্যাটরভাস্টাটিন" },
];
const ROW_B: Chip[] = [
  { brand: "Ace", en: "paracetamol", bn: "প্যারাসিটামল", pair: "para" },
  { brand: "Amdocal", en: "amlodipine", bn: "অ্যামলোডিপিন", pair: "amlo" },
  { brand: "Sergel", en: "esomeprazole", bn: "ইসোমিপ্রাজল", pair: "eso" },
  { brand: "Osartil", en: "losartan", bn: "লোসারটান", pair: "losa" },
  { brand: "Secrin", en: "glimepiride", bn: "গ্লিমেপিরাইড" },
  { brand: "Clofenac", en: "diclofenac", bn: "ডাইক্লোফেনাক" },
  { brand: "Flexi", en: "aceclofenac", bn: "অ্যাসিক্লোফেনাক" },
  { brand: "Rivotril", en: "clonazepam", bn: "ক্লোনাজেপাম" },
];

function Row({ chips, bn, reverse }: { chips: Chip[]; bn: boolean; reverse?: boolean }) {
  // Two identical halves; the track slides by -50% so the loop is seamless.
  const half = (copy: boolean) => (
    <ul className="flex shrink-0 gap-3 pr-3" data-copy={copy || undefined}>
      {chips.map((c) => (
        <li key={c.brand} data-pair={c.pair}
          className="brand-chip flex h-14 shrink-0 items-center gap-3 overflow-hidden rounded-card border border-rule bg-paper pr-4">
          <span aria-hidden className="foil perforated h-full w-3.5" />
          <span className="whitespace-nowrap text-[17px] font-semibold text-ink">{c.brand}</span>
          <span aria-hidden className="text-ink-faint">→</span>
          <span lang={bn ? "bn" : "en"} className="brand-chip-generic whitespace-nowrap rounded-chip bg-neel-tint px-3 py-1 text-[15px] font-medium text-neel">
            {bn ? c.bn : c.en}
          </span>
        </li>
      ))}
    </ul>
  );
  return (
    <div className="marquee-track flex w-max" data-dir={reverse ? "rev" : undefined}>
      {half(false)}
      {half(true)}
    </div>
  );
}

/**
 * The problem in one picture: real brand names, each with the medicine it really is, drifting past in two
 * rows. CSS-only motion, only under html.motion-ok; hover or focus pauses it, and the button (WCAG 2.2.2)
 * and the site-wide Pause motion stop it. Screen readers get one sentence instead of the moving rows.
 */
export function BrandMarquee({ locale, title, caption, sr, pause, play }: {
  locale: string; title: string; caption: string; sr: string; pause: string; play: string;
}) {
  const [paused, setPaused] = useState(false);
  const bn = locale === "bn";
  return (
    <section aria-labelledby="names-h" className="border-t border-rule bg-paper-raised py-[var(--section-y-tight)]">
      <div className="mx-auto flex max-w-[1200px] items-end justify-between gap-4 px-5 sm:px-8">
        <h2 id="names-h" className="font-display text-[clamp(28px,3.4vw,40px)] leading-tight text-ink">{title}</h2>
        <button type="button" onClick={() => setPaused((p) => !p)} aria-pressed={paused}
          className="marquee-toggle inline-flex h-12 shrink-0 items-center gap-2 rounded-chip border border-rule px-4 text-[15px] font-medium text-ink-soft hover:border-rule-strong hover:text-ink">
          {paused ? <Play aria-hidden size={15} /> : <Pause aria-hidden size={15} />} {paused ? play : pause}
        </button>
      </div>
      <p className="sr-only">{sr}</p>
      <div aria-hidden className="marquee mt-8 grid gap-3" data-paused={paused || undefined}>
        <Row chips={ROW_A} bn={bn} />
        <Row chips={ROW_B} bn={bn} reverse />
      </div>
      <p className="mx-auto mt-6 max-w-[1200px] px-5 text-[16px] leading-relaxed text-ink-soft sm:px-8">{caption}</p>
    </section>
  );
}
