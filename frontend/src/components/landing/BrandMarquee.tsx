"use client";

import { Pause, Play } from "lucide-react";
import { useState } from "react";

// Rows from backend/data/brands_seed.csv + generics_bn.csv. Brand names stay Latin, as printed on the strip.
const SHARED: [string, string, string][] = [
  ["Napa · Ace", "paracetamol", "প্যারাসিটামল"],
  ["Camlodin · Amdocal", "amlodipine", "অ্যামলোডিপিন"],
  ["Angilock · Osartil", "losartan", "লোসারটান"],
  ["Maxpro · Sergel", "esomeprazole", "ইসোমিপ্রাজল"],
];
const SINGLE: [string, string, string][] = [
  ["Comet", "metformin", "মেটফরমিন"],
  ["Seclo", "omeprazole", "ওমিপ্রাজল"],
  ["Secrin", "glimepiride", "গ্লিমেপিরাইড"],
  ["Ecosprin", "aspirin", "অ্যাসপিরিন"],
  ["Atova", "atorvastatin", "অ্যাটরভাস্টাটিন"],
  ["Clofenac", "diclofenac", "ডাইক্লোফেনাক"],
  ["Flexi", "aceclofenac", "অ্যাসিক্লোফেনাক"],
  ["Rivotril", "clonazepam", "ক্লোনাজেপাম"],
  ["Tryptin", "amitriptyline", "অ্যামিট্রিপটিলিন"],
];

function Row({ rows, bn, reverse }: { rows: typeof SHARED; bn: boolean; reverse?: boolean }) {
  // Two identical halves; the track slides by -50% so the loop is seamless. The copy is hidden from screen readers.
  const half = (copy: boolean) => (
    <ul aria-hidden={copy || undefined} className="flex shrink-0 gap-4 pr-4">
      {rows.map(([brands, en, bnName]) => (
        <li key={brands} className="flex h-14 shrink-0 items-center gap-3 overflow-hidden rounded-card border border-rule bg-paper-raised pr-4">
          <span aria-hidden className="foil perforated h-full w-3.5" />
          <span className="whitespace-nowrap text-[17px] font-semibold text-ink">{brands}</span>
          <span aria-hidden className="stitch-x w-6" />
          <span lang={bn ? "bn" : "en"} className="whitespace-nowrap rounded-chip bg-neel-tint px-3 py-1 text-[15px] font-medium text-neel">
            {bn ? bnName : en}
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

/** Many brand names, one medicine: real rows of the brand table drifting past. Pausable (WCAG 2.2.2). */
export function BrandMarquee({ locale, title, pause, play }: { locale: string; title: string; pause: string; play: string }) {
  const [paused, setPaused] = useState(false);
  const bn = locale === "bn";
  return (
    <section aria-labelledby="names-h" className="border-t border-rule py-12 lg:py-16">
      <div className="mx-auto flex max-w-[1200px] items-center justify-between gap-4 px-5 sm:px-8">
        <h2 id="names-h" className="text-[17px] font-semibold text-ink-soft">{title}</h2>
        <button type="button" onClick={() => setPaused((p) => !p)} aria-pressed={paused}
          className="marquee-toggle inline-flex h-11 shrink-0 items-center gap-2 rounded-chip border border-rule px-4 text-[15px] font-medium text-ink-soft hover:border-rule-strong hover:text-ink">
          {paused ? <Play aria-hidden size={15} /> : <Pause aria-hidden size={15} />} {paused ? play : pause}
        </button>
      </div>
      <div className="marquee mt-6 grid gap-4" data-paused={paused || undefined}>
        <Row rows={SHARED} bn={bn} />
        <Row rows={SINGLE} bn={bn} reverse />
      </div>
    </section>
  );
}
