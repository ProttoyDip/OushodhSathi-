"use client";

import { ArrowLeft, ArrowRight, Camera, Check, Keyboard, Stethoscope } from "lucide-react";
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
  { ch: "The shelf", chBn: "তাক", who: "Rahima's home, Cumilla", en: "Rahima Begum, 68, collects medicines from three places.", bn: "রহিমা বেগম, ৬৮ — তিন জায়গা থেকে ওষুধ আসে।" },
  { ch: "Scan", chBn: "ছবি", who: "Family app · phone camera", en: "Her daughter photographs the whole shelf.", bn: "মেয়ে পুরো তাকের ছবি তোলেন।" },
  { ch: "The list", chBn: "তালিকা", who: "Vision model reads every strip", en: "The list assembles itself.", bn: "তালিকা নিজে থেকেই সাজানো হয়।" },
  { ch: "Duplicate", chBn: "একই ওষুধ", who: "Rules engine · no AI", en: "Different names, same medicine: paracetamol, twice.", bn: "নাম আলাদা, ওষুধ একই — প্যারাসিটামল, দুইবার।" },
  { ch: "Review", chBn: "যাচাই", who: "Pharmacist dashboard", en: "A pharmacist confirms the finding, with a note.", bn: "একজন ফার্মাসিস্ট নিশ্চিত করেন, নোটসহ।" },
  { ch: "Family", chBn: "পরিবার", who: "Her daughter's phone, Toronto", en: "Only now does the family see it, in simple Bangla.", bn: "এরপরই পরিবার দেখতে পায়, সহজ বাংলায়।" },
  { ch: "Passport", chBn: "পাসপোর্ট", who: "Printed, carried to every visit", en: "A passport for every doctor visit.", bn: "প্রতিবার ডাক্তারের কাছে নেওয়ার পাসপোর্ট।" },
  { ch: "Report", chBn: "রিপোর্ট", who: "Weekly report", en: "And the weekly report keeps watch.", bn: "সাপ্তাহিক রিপোর্টে রক্তচাপের খোঁজ।" },
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
        <header className="mx-auto flex w-full max-w-[1680px] items-center justify-between gap-4 px-8 py-5 lg:px-16">
          <Wordmark />
          <DemoTag />
        </header>

        <main className="mx-auto grid w-full max-w-[1680px] flex-1 grid-cols-[minmax(0,1fr)] items-center gap-10 px-8 pb-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:gap-20 lg:px-16">
          <div key={`cap-${step}`} className="max-w-[720px]" style={{ animation: "assemble 260ms var(--ease-out-quint) both" }}>
            <p className="flex items-baseline gap-3 text-ink-faint">
              <span className="tabular font-display text-[28px] leading-none text-teal">{String(step + 1).padStart(2, "0")}</span>
              <span className="text-[15px] font-semibold uppercase tracking-[0.14em]">{s.ch}</span>
              <span lang="bn" className="font-bn text-[16px]">{s.chBn}</span>
            </p>
            <h1 lang="en" className="mt-5 font-display text-[clamp(40px,4.4vw,80px)] leading-[1.02] text-ink">{s.en}</h1>
            <p lang="bn" className="mt-5 font-bn-display text-[clamp(24px,2.3vw,40px)] leading-snug text-ink-soft">{s.bn}</p>
            <p className="mt-8 inline-flex items-center gap-2 border-t border-rule pt-4 text-[16px] text-ink-soft">
              <span aria-hidden className="h-2 w-2 rounded-full bg-teal" /> {s.who}
            </p>
          </div>

          <div className="relative flex min-h-[520px] min-w-0 items-center justify-center text-[18px]">
            <Stage key={step} step={step} passportUrl={origin ? `${origin}/passport/1` : undefined} />
          </div>
        </main>

        <footer className="mx-auto flex w-full max-w-[1680px] items-end justify-between gap-6 px-8 pb-6 lg:px-16">
          <ol className="grid min-w-0 flex-1 grid-cols-8 gap-2" aria-label="Progress">
            {STEPS.map((st, i) => (
              <li key={i} className="min-w-0">
                <button
                  type="button"
                  aria-label={`Step ${i + 1}: ${st.ch}`}
                  aria-current={i === step ? "step" : undefined}
                  onClick={() => setStep(i)}
                  className="group block w-full pt-2 text-left"
                >
                  <span className={cx("block h-1 rounded-chip transition-colors duration-200", i < step ? "bg-teal/45" : i === step ? "bg-teal" : "bg-rule")} />
                  <span className={cx("mt-2 hidden truncate text-[13px] font-medium md:block", i === step ? "text-ink" : "text-ink-faint group-hover:text-ink-soft")}>{st.ch}</span>
                </button>
              </li>
            ))}
          </ol>
          <div className="flex shrink-0 items-center gap-3 text-[15px] text-ink-faint">
            <span className="hidden items-center gap-2 lg:inline-flex"><Keyboard aria-hidden size={18} /> → next · ← back</span>
            <button type="button" onClick={() => go(-1)} aria-label="Back" className="inline-flex h-12 w-12 items-center justify-center rounded-full border border-rule text-ink"><ArrowLeft aria-hidden size={18} /></button>
            <button type="button" onClick={() => go(1)} aria-label="Next" className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-teal text-on-teal"><ArrowRight aria-hidden size={18} /></button>
          </div>
        </footer>
      </div>
    </NextIntlClientProvider>
  );
}

/** A phone outline for screens the family sees. */
function Phone({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <figure className="demo-fit w-full max-w-[420px]" style={{ animation: "assemble 280ms var(--ease-out-quint) both" }}>
      <div className="rounded-[40px] border border-rule-strong bg-paper-sunk p-3 shadow-soft">
        <div className="overflow-hidden rounded-[30px] border border-rule bg-paper">
          <div className="flex items-center justify-between px-5 pb-1 pt-3 text-[12px] font-medium text-ink-faint">
            <span className="tabular">9:41</span><span aria-hidden className="h-1.5 w-16 rounded-chip bg-rule" /><span>{label}</span>
          </div>
          <div className="relative max-h-[700px] overflow-hidden px-4 pb-5 pt-2">
            {children}
            <div aria-hidden className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-paper to-transparent" />
          </div>
        </div>
      </div>
    </figure>
  );
}

function Stage({ step, passportUrl }: { step: number; passportUrl?: string }) {
  if (step <= 1) {
    // the messy shelf: strips in a pile; step 2 adds the camera frame around it
    return (
      <div className="relative h-[480px] w-full max-w-[500px]">
        {SHELF.map((it, i) => (
          <div
            key={it.id}
            className="absolute left-1/2 top-[60px] w-[340px] transition-transform duration-500"
            style={{ transform: `translate(calc(-50% + ${PILE[i].x}px), ${PILE[i].y}px) rotate(${PILE[i].r}deg)`, zIndex: i }}
          >
            <StripCard item={it} density="compact" />
          </div>
        ))}
        {step === 1 && (
          <div aria-hidden className="pointer-events-none absolute -inset-x-6 -inset-y-2 z-20 rounded-[28px] border-[3px] border-teal" style={{ animation: "assemble 240ms var(--ease-out-quint) both" }}>
            {["left-3 top-3 border-l-4 border-t-4", "right-3 top-3 border-r-4 border-t-4", "bottom-3 left-3 border-b-4 border-l-4", "bottom-3 right-3 border-b-4 border-r-4"].map((c) => (
              <span key={c} className={`absolute h-9 w-9 rounded-[3px] border-teal ${c}`} />
            ))}
            <span className="absolute -bottom-5 left-1/2 inline-flex h-10 -translate-x-1/2 items-center gap-2 rounded-chip bg-teal px-4 text-[15px] font-semibold text-on-teal shadow-soft">
              <Camera aria-hidden size={17} /> {SHELF.length} strips in view
            </span>
          </div>
        )}
      </div>
    );
  }
  if (step === 2) {
    return (
      <div className="demo-fit-sm grid w-full max-w-[880px] gap-4 sm:grid-cols-2">
        {SHELF.map((it, i) => (
          <div key={it.id} style={{ animation: `assemble 260ms var(--ease-out-quint) ${i * 120}ms both` }}>
            <StripCard item={it} density="compact" />
          </div>
        ))}
      </div>
    );
  }
  if (step === 3) {
    // the hero moment: the pair snaps together, everything else steps back
    return (
      <div className="w-full max-w-[860px]">
        {/* side by side from tablet up; stacked on phones (display:none keeps one copy in the a11y tree) */}
        <DuplicateConnector orientation="horizontal" label="দুটোই প্যারাসিটামল" delay={150} className="hidden sm:block">
          <StripCard item={DEMO_ITEMS.napa} highlight="red" />
          <StripCard item={DEMO_ITEMS.ace} highlight="red" />
        </DuplicateConnector>
        <DuplicateConnector label="দুটোই প্যারাসিটামল" delay={150} className="sm:hidden">
          <StripCard item={DEMO_ITEMS.napa} density="compact" highlight="red" />
          <StripCard item={DEMO_ITEMS.ace} density="compact" highlight="red" />
        </DuplicateConnector>
        <p lang="en" className="mt-5 text-center text-[17px] text-ink-soft" style={{ animation: "assemble 260ms var(--ease-out-quint) 650ms both" }}>
          From the <b className="font-semibold text-ink">local drug shop</b> and the <b className="font-semibold text-ink">village doctor</b>: two prescribers, one medicine.
        </p>
        <div aria-hidden className="mt-8 hidden grid-cols-2 gap-4 opacity-40 saturate-50 sm:grid">
          <StripCard item={DEMO_ITEMS.camlodin} density="compact" />
          <StripCard item={comet} density="compact" />
        </div>
      </div>
    );
  }
  if (step === 4) {
    return (
      <div lang="en" className="demo-fit-sm w-full max-w-[720px] overflow-hidden rounded-card border border-rule-strong bg-paper-raised text-[15px] shadow-soft" style={{ animation: "assemble 280ms var(--ease-out-quint) both" }}>
        <div className="flex items-center justify-between border-b border-rule bg-paper-sunk/60 px-6 py-3 text-[14px] text-ink-soft">
          <span className="inline-flex items-center gap-2 font-semibold text-ink"><Stethoscope aria-hidden size={17} /> Clinical review · queue</span>
          <span className="flex items-center gap-1.5">
            {["J", "K", "C", "D", "N"].map((k) => (
              <kbd key={k} className={cx("inline-flex h-6 min-w-6 items-center justify-center rounded border px-1.5 font-mono text-[12px]", k === "C" ? "border-teal bg-teal text-on-teal" : "border-rule-strong bg-paper-raised")}>{k}</kbd>
            ))}
          </span>
        </div>
        <div className="p-6">
          <div className="flex flex-wrap items-center gap-3">
            <SeverityBadge severity="red" label="Red · for the doctor" />
            <span className="font-display text-[32px] leading-none">Same generic, two brands</span>
          </div>
          <p className="mt-2 text-ink-soft">Rahima Begum, 68 · rule <code className="font-mono text-[14px]">DUPLICATE_GENERIC</code> · source: brand table</p>
          <div className="mt-5">
            <DuplicateConnector orientation="horizontal" label="Both are paracetamol" animate={false} className="hidden sm:block">
              <StripCard item={DEMO_ITEMS.napa} density="compact" highlight="red" />
              <StripCard item={DEMO_ITEMS.ace} density="compact" highlight="red" />
            </DuplicateConnector>
            <DuplicateConnector label="Both are paracetamol" animate={false} className="sm:hidden">
              <StripCard item={DEMO_ITEMS.napa} density="compact" highlight="red" />
              <StripCard item={DEMO_ITEMS.ace} density="compact" highlight="red" />
            </DuplicateConnector>
          </div>
          <p className="mt-5 font-semibold text-ink">Note to the family</p>
          <p className="mt-1.5 rounded-md border border-rule-strong bg-paper px-3.5 py-2.5 text-ink">{DEMO_FLAG.note}</p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <span className="inline-flex h-12 items-center gap-2 rounded-card bg-teal px-5 font-semibold text-on-teal" style={{ animation: "settle 260ms var(--ease-out-quint) 500ms both" }}>
              <Check aria-hidden size={18} strokeWidth={2.5} /> Confirmed by Demo pharmacist
            </span>
            <span className="text-ink-faint">Every decision is recorded with the reviewer&rsquo;s name.</span>
          </div>
        </div>
      </div>
    );
  }
  if (step === 5) return <Phone label="ওষুধসাথী"><FlagResult flag={DEMO_FLAG} /></Phone>;
  if (step === 6) return <div className="demo-fit w-full max-w-[580px] rotate-[0.6deg]" style={{ animation: "settle 260ms var(--ease-out-quint) both" }}><MedicinePassport passport={DEMO_PASSPORT} url={passportUrl} /></div>;
  const first = DEMO_BP[0];
  const last = DEMO_BP[DEMO_BP.length - 1];
  return (
    <div className="w-full max-w-[640px] rounded-card border border-rule bg-paper-raised p-7 shadow-soft" style={{ animation: "assemble 260ms var(--ease-out-quint) both" }}>
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <p className="font-bn-display text-[26px]">রক্তচাপ — গত ৭ দিন</p>
        {first && last && (
          <p lang="en" className="tabular text-[15px] text-ink-soft">
            {first.systolic}/{first.diastolic} → <b className="font-semibold text-ink">{last.systolic}/{last.diastolic}</b> mmHg
          </p>
        )}
      </div>
      <div className="mt-4"><BPTrend readings={DEMO_BP} height={300} /></div>
      <p className="mt-4 border-t border-rule pt-4 text-[15px] text-ink-soft">Sent to the family every Friday. Target 140/90 marked on the chart.</p>
    </div>
  );
}
