"use client";

import { useState } from "react";
import { BPTrend } from "@/components/BPTrend";
import { BrandMark, Wordmark } from "@/components/BrandMark";
import { buttonStyles, DemoTag, LangToggle, ThemeToggle } from "@/components/Chrome";
import { DuplicateConnector } from "@/components/DuplicateConnector";
import { FlagResult } from "@/components/FlagResult";
import { MedicinePassport } from "@/components/MedicinePassport";
import { ReviewRow } from "@/components/ReviewRow";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StripCard } from "@/components/StripCard";
import { DEMO_BP, DEMO_FLAG, DEMO_ITEMS, DEMO_PASSPORT, DEMO_PENDING_FLAGS } from "@/lib/demoData";

const DEMO_NOW = Date.parse("2026-10-26T09:00:00+00:00");

const COLORS: [string, string][] = [
  ["paper", "Page ground"], ["paper-raised", "Cards"], ["paper-sunk", "Insets"], ["ink", "Text"],
  ["ink-soft", "Secondary text"], ["ink-faint", "Captions"], ["rule", "Dividers"], ["foil", "Strip foil"],
  ["teal", "Primary action"], ["teal-tint", "Selection, chips"], ["red", "Doctor review"], ["red-tint", "Red surface"],
  ["amber", "Pharmacist review"], ["amber-tint", "Amber surface"], ["green", "No problem found"], ["green-tint", "Green surface"],
];

export default function Styleguide() {
  const [replay, setReplay] = useState(0);
  return (
    <div className="mx-auto max-w-[1180px] px-6 pb-24 pt-8">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-rule pb-6">
        <div>
          <div className="flex flex-wrap items-center gap-3"><Wordmark /><DemoTag label="Examples use the demo household — invented data" /></div>
          <h1 className="mt-4 font-display text-[56px] leading-none">The pharmacist&rsquo;s ledger</h1>
          <p className="mt-2 max-w-[60ch] text-lg text-ink-soft">
            Design system for OushodhSathi: prescription paper, medicine-strip foil, and severity that is always colour, icon and word.
          </p>
        </div>
        <div className="flex items-center gap-2"><ThemeToggle /><LangToggle /></div>
      </header>

      <Section title="Colour tokens" note="Every colour is a CSS variable with a light and a dark value. Toggle the theme to check both.">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {COLORS.map(([token, role]) => (
            <div key={token} className="overflow-hidden rounded-card border border-rule bg-paper-raised">
              <div className="h-16 border-b border-rule" style={{ background: `var(--${token})` }} />
              <div className="p-3">
                <p className="font-mono text-[13px] text-ink">--{token}</p>
                <p className="text-sm text-ink-soft">{role}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 h-12 rounded-card foil" aria-label="Foil material" />
      </Section>

      <Section title="Type" note="Bangla: Tiro Bangla display, Hind Siliguri body (line-height 1.6). Latin: Instrument Serif display, Instrument Sans body. Numbers are tabular.">
        <div className="grid gap-6 sm:grid-cols-2">
          <div>
            <p lang="bn" className="font-bn-display text-[44px] leading-[1.15]">ওষুধের পাসপোর্ট</p>
            <p lang="bn" className="mt-2 text-[18px]">বাড়ির সব ওষুধের পাতা, বাক্স আর প্রেসক্রিপশনের ছবি তুলুন। একজন ফার্মাসিস্ট বা ডাক্তার প্রতিটি বিষয় নিশ্চিত করেন।</p>
          </div>
          <div>
            <p className="font-display text-[44px] leading-[1.05]">Medicine passport</p>
            <p className="mt-2 text-[18px]">AI for perception, rules and humans for judgement.</p>
            <p className="tabular mt-3 font-display text-[34px]">168/98 → 142/88</p>
          </div>
        </div>
      </Section>

      <Section title="Severity badge" note="Three sizes. Never colour alone.">
        <div className="grid gap-3">
          {(["sm", "md", "lg"] as const).map((size) => (
            <div key={size} className="flex flex-wrap items-center gap-3">
              <SeverityBadge severity="red" size={size} />
              <SeverityBadge severity="amber" size={size} />
              <SeverityBadge severity="green" size={size} />
            </div>
          ))}
        </div>
      </Section>

      <Section title="StripCard" note="Normal, low confidence (dashed + যাচাই করুন), not recognised, web match (unverified, with source), compact.">
        <div className="grid gap-4 sm:grid-cols-2">
          <StripCard item={DEMO_ITEMS.napa} />
          <StripCard item={DEMO_ITEMS.tryptin} />
          <StripCard item={DEMO_ITEMS.unknown} />
          <StripCard item={DEMO_ITEMS.web} />
          <StripCard item={DEMO_ITEMS.camlodin} density="compact" />
          <StripCard item={DEMO_ITEMS.amdocal} density="compact" highlight="amber" />
        </div>
      </Section>

      <Section
        title="DuplicateConnector"
        note="The hero moment: cards slide together, the bracket draws itself, the label lands."
        action={<button type="button" className={buttonStyles.secondary} onClick={() => setReplay((r) => r + 1)}>Replay</button>}
      >
        <div key={replay} className="grid gap-10 lg:grid-cols-[400px_1fr]">
          <DuplicateConnector label="দুটোই প্যারাসিটামল">
            <StripCard item={DEMO_ITEMS.napa} density="compact" highlight="red" />
            <StripCard item={DEMO_ITEMS.ace} density="compact" highlight="red" />
          </DuplicateConnector>
          <DuplicateConnector orientation="horizontal" label="Both are amlodipine" delay={150}>
            <StripCard item={DEMO_ITEMS.camlodin} density="compact" highlight="red" />
            <StripCard item={DEMO_ITEMS.amdocal} density="compact" highlight="red" />
          </DuplicateConnector>
        </div>
      </Section>

      <Section title="Confirmed finding (family view)">
        <div className="max-w-[480px] text-[18px]"><FlagResult flag={DEMO_FLAG} /></div>
      </Section>

      <Section title="ReviewRow" note="Queue rows: severity, rule, medicines, patient age, routed to, time waiting.">
        <div role="listbox" aria-label="Example queue" className="grid max-w-[380px] gap-1">
          {DEMO_PENDING_FLAGS.map((f, i) => <ReviewRow key={f.id} flag={f} selected={i === 0} now={DEMO_NOW} />)}
        </div>
      </Section>

      <Section title="BPTrend" note="Seven days with the 140/90 target as labelled reference lines.">
        <div className="max-w-[560px] rounded-card border border-rule bg-paper-raised p-5"><BPTrend readings={DEMO_BP} /></div>
      </Section>

      <Section title="MedicinePassport" note="A5, prints in black and white.">
        <MedicinePassport passport={DEMO_PASSPORT} url="https://example.org/passport/1" />
      </Section>

      <Section title="Buttons and chrome">
        <div className="grid max-w-[480px] gap-3">
          <button type="button" className={buttonStyles.primary}>ওষুধ স্ক্যান করুন</button>
          <button type="button" className={buttonStyles.primary} disabled>Disabled primary</button>
          <div className="flex flex-wrap gap-3">
            <button type="button" className={buttonStyles.secondary}>Secondary</button>
            <button type="button" className={buttonStyles.quiet}>Quiet</button>
          </div>
          <div className="flex items-center gap-3"><BrandMark size={40} /><DemoTag /></div>
        </div>
      </Section>
    </div>
  );
}

function Section({ title, note, action, children }: { title: string; note?: string; action?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="border-b border-rule py-10">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-[32px] leading-none">{title}</h2>
          {note && <p className="mt-2 max-w-[70ch] text-ink-soft">{note}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
