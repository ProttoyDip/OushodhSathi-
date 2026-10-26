"use client";

import { ArrowLeft, ArrowRight, Check, Keyboard } from "lucide-react";
import { NextIntlClientProvider } from "next-intl";
import { useCallback, useEffect, useState } from "react";
import bn from "../../../messages/bn.json";
import { BPTrend } from "@/components/BPTrend";
import { Wordmark } from "@/components/BrandMark";
import { DemoTag } from "@/components/Chrome";
import { DuplicateConnector } from "@/components/DuplicateConnector";
import { FlagResult } from "@/components/FlagResult";
import { MedicinePassport } from "@/components/MedicinePassport";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StripCard } from "@/components/StripCard";
import { DEMO_BP, DEMO_FLAG, DEMO_ITEMS, DEMO_PASSPORT } from "@/lib/demoData";
import { cx } from "@/lib/format";

const comet = { ...DEMO_ITEMS.camlodin, id: 9, brand: "Comet", strength: "500 mg", generic: "metformin", drug_class: "biguanide", expiry: "2027-05" };
const SHELF = [DEMO_ITEMS.napa, DEMO_ITEMS.camlodin, DEMO_ITEMS.ace, comet, DEMO_ITEMS.amdocal, { ...DEMO_ITEMS.tryptin, confirmed: true }];
const PILE = [
  { r: -14, x: -40, y: 10 }, { r: 9, x: 60, y: -30 }, { r: -4, x: 10, y: 60 },
  { r: 17, x: -70, y: 90 }, { r: -9, x: 80, y: 120 }, { r: 6, x: -10, y: 160 },
];

const STEPS = [
  { en: "Rahima Begum, 68, collects medicines from three places.", bn: "রহিমা বেগম, ৬৮ — তিন জায়গা থেকে ওষুধ আসে।" },
  { en: "Her daughter photographs the whole shelf.", bn: "মেয়ে পুরো তাকের ছবি তোলেন।" },
  { en: "The list assembles itself.", bn: "তালিকা নিজে থেকেই সাজানো হয়।" },
  { en: "Different names, same medicine: paracetamol, twice.", bn: "নাম আলাদা, ওষুধ একই — প্যারাসিটামল, দুইবার।" },
  { en: "A pharmacist confirms the finding, with a note.", bn: "একজন ফার্মাসিস্ট নিশ্চিত করেন, নোটসহ।" },
  { en: "Only now does the family see it, in simple Bangla.", bn: "এরপরই পরিবার দেখতে পায়, সহজ বাংলায়।" },
  { en: "A passport for every doctor visit.", bn: "প্রতিবার ডাক্তারের কাছে নেওয়ার পাসপোর্ট।" },
  { en: "And the weekly report keeps watch.", bn: "সাপ্তাহিক রিপোর্টে রক্তচাপের খোঁজ।" },
];

/** A keyboard-paced walkthrough of the hero flow for recording. → / Space next, ← back. */
export default function DemoWalkthrough() {
  const [step, setStep] = useState(0);
  const [origin, setOrigin] = useState("");
  useEffect(() => setOrigin(location.origin), []);
  const go = useCallback((d: number) => setStep((s) => Math.min(STEPS.length - 1, Math.max(0, s + d))), []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (["ArrowRight", " ", "PageDown", "Enter"].includes(e.key)) { e.preventDefault(); go(1); }
      if (["ArrowLeft", "PageUp", "Backspace"].includes(e.key)) { e.preventDefault(); go(-1); }
      if (e.key === "Home") setStep(0);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go]);
  useEffect(() => {
    const s = Number(new URLSearchParams(location.search).get("step"));
    if (s > 0) setStep(Math.min(STEPS.length - 1, s));
  }, []);

  const s = STEPS[step];
  return (
    <NextIntlClientProvider locale="bn" messages={bn} timeZone="Asia/Dhaka">
      <div className="flex min-h-dvh flex-col overflow-x-hidden">
        <header className="flex items-center justify-between gap-4 px-8 py-5">
          <Wordmark />
          <DemoTag />
        </header>

        <main className="grid flex-1 grid-cols-[minmax(0,1fr)] items-center gap-10 px-8 pb-6 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:px-16">
          <div key={`cap-${step}`} style={{ animation: "assemble 260ms var(--ease-out-quint) both" }}>
            <p className="tabular text-[15px] font-semibold text-ink-faint">{step + 1} / {STEPS.length}</p>
            <h1 lang="en" className="mt-3 font-display text-[clamp(40px,4.6vw,72px)] leading-[1.02] text-ink">{s.en}</h1>
            <p lang="bn" className="mt-4 font-bn-display text-[clamp(24px,2.4vw,36px)] leading-snug text-ink-soft">{s.bn}</p>
          </div>

          <div className="relative flex min-h-[560px] min-w-0 items-center justify-center text-[18px]">
            <Stage step={step} passportUrl={origin ? `${origin}/passport/1` : undefined} />
          </div>
        </main>

        <footer className="flex items-center justify-between gap-4 px-8 pb-6">
          <ol className="flex gap-2" aria-label="Progress">
            {STEPS.map((_, i) => (
              <li key={i}>
                <button
                  type="button"
                  aria-label={`Step ${i + 1}`}
                  aria-current={i === step}
                  onClick={() => setStep(i)}
                  className={cx("block h-2.5 rounded-chip transition-all duration-200", i === step ? "w-8 bg-teal" : "w-2.5 bg-rule-strong")}
                />
              </li>
            ))}
          </ol>
          <div className="flex items-center gap-3 text-[15px] text-ink-faint">
            <Keyboard aria-hidden size={18} /> → next · ← back
            <button type="button" onClick={() => go(-1)} aria-label="Back" className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-rule text-ink"><ArrowLeft aria-hidden size={18} /></button>
            <button type="button" onClick={() => go(1)} aria-label="Next" className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-teal text-on-teal"><ArrowRight aria-hidden size={18} /></button>
          </div>
        </footer>
      </div>
    </NextIntlClientProvider>
  );
}

function Stage({ step, passportUrl }: { step: number; passportUrl?: string }) {
  if (step <= 1) {
    // the messy shelf: strips in a pile; step 1 adds the camera frame
    return (
      <div className="relative h-[520px] w-full max-w-[460px]">
        {SHELF.map((it, i) => (
          <div
            key={it.id}
            className="absolute left-1/2 top-4 w-[330px] transition-transform duration-500"
            style={{ transform: `translate(calc(-50% + ${PILE[i].x}px), ${PILE[i].y}px) rotate(${PILE[i].r}deg)`, zIndex: i }}
          >
            <StripCard item={it} density="compact" />
          </div>
        ))}
        {step === 1 && (
          <div aria-hidden className="pointer-events-none absolute -inset-4 z-20 rounded-[24px] border-[3px] border-teal" style={{ animation: "assemble 240ms var(--ease-out-quint) both" }}>
            {["left-3 top-3 border-l-4 border-t-4", "right-3 top-3 border-r-4 border-t-4", "bottom-3 left-3 border-b-4 border-l-4", "bottom-3 right-3 border-b-4 border-r-4"].map((c) => (
              <span key={c} className={`absolute h-8 w-8 border-teal ${c}`} />
            ))}
          </div>
        )}
      </div>
    );
  }
  if (step === 2) {
    return (
      <div className="grid w-full max-w-[460px] gap-3">
        {SHELF.slice(0, 5).map((it, i) => (
          <div key={it.id} style={{ animation: `assemble 260ms var(--ease-out-quint) ${i * 140}ms both` }}>
            <StripCard item={it} density="compact" />
          </div>
        ))}
      </div>
    );
  }
  if (step === 3) {
    return (
      <div className="grid w-full max-w-[460px] gap-3">
        <DuplicateConnector label="দুটোই প্যারাসিটামল" delay={150}>
          <StripCard item={DEMO_ITEMS.napa} density="compact" highlight="red" />
          <StripCard item={DEMO_ITEMS.ace} density="compact" highlight="red" />
        </DuplicateConnector>
        <div style={{ animation: "settle 240ms var(--ease-out-quint) 200ms both" }}><StripCard item={DEMO_ITEMS.camlodin} density="compact" /></div>
      </div>
    );
  }
  if (step === 4) {
    return (
      <div lang="en" className="w-full max-w-[640px] rounded-card border border-rule bg-paper-raised p-6 text-[15px] shadow-soft">
        <div className="flex flex-wrap items-center gap-3">
          <SeverityBadge severity="red" label="Red · for the doctor" />
          <span className="font-display text-[30px] leading-none">Same generic, two brands</span>
        </div>
        <p className="mt-2 text-ink-soft">Rahima Begum, 68 · rule DUPLICATE_GENERIC · source: brand table</p>
        <div className="mt-5">
          <DuplicateConnector orientation="horizontal" label="Both are paracetamol" animate={false}>
            <StripCard item={DEMO_ITEMS.napa} density="compact" highlight="red" />
            <StripCard item={DEMO_ITEMS.ace} density="compact" highlight="red" />
          </DuplicateConnector>
        </div>
        <p className="mt-5 font-semibold text-ink">Note</p>
        <p className="mt-1 rounded-md border border-rule-strong bg-paper px-3 py-2 text-ink">{DEMO_FLAG.note}</p>
        <div className="mt-4 flex items-center gap-3">
          <span className="inline-flex h-11 items-center gap-2 rounded-card bg-teal px-5 font-semibold text-on-teal" style={{ animation: "settle 260ms var(--ease-out-quint) 500ms both" }}>
            <Check aria-hidden size={18} strokeWidth={2.5} /> Confirmed by Demo pharmacist
          </span>
          <span className="text-ink-faint">decided in under 30 seconds</span>
        </div>
      </div>
    );
  }
  if (step === 5) return <div className="w-full max-w-[460px]"><FlagResult flag={DEMO_FLAG} /></div>;
  if (step === 6) return <div className="w-full max-w-[560px]" style={{ animation: "settle 260ms var(--ease-out-quint) both" }}><MedicinePassport passport={DEMO_PASSPORT} url={passportUrl} /></div>;
  return (
    <div className="w-full max-w-[560px] rounded-card border border-rule bg-paper-raised p-6" style={{ animation: "assemble 260ms var(--ease-out-quint) both" }}>
      <p className="font-bn-display text-[24px]">রক্তচাপ — গত ৭ দিন</p>
      <div className="mt-3"><BPTrend readings={DEMO_BP} height={280} /></div>
    </div>
  );
}
