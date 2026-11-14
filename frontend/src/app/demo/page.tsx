"use client";

import { AlertTriangle, ArrowLeft, ArrowRight, BookOpen, Camera, Check, Keyboard, MessageSquareReply, Minus, Moon, Phone as PhoneIcon, Plus, Printer, Send, ShieldAlert, ShieldQuestion, Sparkles, Stethoscope, Sun, Sunrise, Volume2 } from "lucide-react";
import { NextIntlClientProvider, useLocale, useTranslations } from "next-intl";
import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import { type ReactNode, useCallback, useEffect, useState, useSyncExternalStore } from "react";
import bn from "../../../messages/bn.json";
import { BPTrend } from "@/components/BPTrend";
import { Wordmark } from "@/components/BrandMark";
import { DemoTag, LangToggle, ThemeToggle } from "@/components/Chrome";
import { stickyBar } from "@/lib/layout";
import { JudgeBar } from "@/components/JudgeBar";
import { DuplicateConnector } from "@/components/DuplicateConnector";
import { FlagResult } from "@/components/FlagResult";
import { MedicinePassport } from "@/components/MedicinePassport";
import { SathiMark } from "@/components/sathi/SathiMark";
import { SPRING_TRAVEL } from "@/components/Motion";
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
  { ch: "The shelf", chBn: "তাক", who: "Rahima's home, Cumilla", whoBn: "রহিমার বাড়ি, কুমিল্লা", en: "Rahima Begum, 68, collects medicines from three places.", bn: "রহিমা বেগম, ৬৮ — তিন জায়গা থেকে ওষুধ আসে।" },
  { ch: "Scan", chBn: "ছবি", who: "Family app · phone camera", whoBn: "পরিবারের অ্যাপ · ফোনের ক্যামেরা", en: "Her daughter photographs the whole shelf.", bn: "মেয়ে পুরো তাকের ছবি তোলেন।" },
  { ch: "The list", chBn: "তালিকা", who: "Vision model reads every strip", whoBn: "ভিশন মডেল প্রতিটি পাতা পড়ে", en: "The list assembles itself.", bn: "তালিকা নিজে থেকেই সাজানো হয়।" },
  { ch: "Duplicate", chBn: "একই ওষুধ", who: "Rules engine · no AI", whoBn: "নিয়ম-ইঞ্জিন · কোনো এআই নেই", en: "Different names, same medicine: paracetamol, twice.", bn: "নাম আলাদা, ওষুধ একই — প্যারাসিটামল, দুইবার।" },
  { ch: "Review", chBn: "যাচাই", who: "Pharmacist dashboard", whoBn: "ফার্মাসিস্টের ড্যাশবোর্ড", en: "A pharmacist confirms the finding, with a note.", bn: "একজন ফার্মাসিস্ট নিশ্চিত করেন, নোটসহ।" },
  { ch: "Family", chBn: "পরিবার", who: "Her daughter's phone, Toronto", whoBn: "মেয়ের ফোন, টরন্টো", en: "Only now does the family see it, in simple Bangla.", bn: "এরপরই পরিবার দেখতে পায়, সহজ বাংলায়।" },
  { ch: "Passport", chBn: "পাসপোর্ট", who: "Printed, carried to every visit", whoBn: "ছাপানো, প্রতিবার সাথে নেওয়া", en: "A passport for every doctor visit.", bn: "প্রতিবার ডাক্তারের কাছে নেওয়ার পাসপোর্ট।" },
  { ch: "Emergency", chBn: "জরুরি", who: "Passport QR · read-only, no login", whoBn: "পাসপোর্টের কিউআর · শুধু পড়া, লগইন নেই", en: "In an emergency, the QR opens what a doctor needs first.", bn: "জরুরি অবস্থায় কিউআর খোলে, ডাক্তারের প্রথমে যা জানা দরকার।" },
  { ch: "Today", chBn: "আজকের ওষুধ", who: "Works without reading", whoBn: "পড়তে না পারলেও চলে", en: "For a parent who can't read: pictures, tablets drawn, read aloud.", bn: "যিনি পড়তে পারেন না, তাঁর জন্য: ছবি, আঁকা বড়ি, পড়ে শোনানো।" },
  { ch: "Report", chBn: "রিপোর্ট", who: "Weekly report · BP from a photo", whoBn: "সাপ্তাহিক রিপোর্ট · ছবি থেকে রক্তচাপ", en: "Blood pressure, typed or read from a photo of the machine.", bn: "রক্তচাপ লিখে, বা মেশিনের ছবি থেকে পড়ে।" },
  { ch: "Sathi", chBn: "সাথী", who: "In-app helper · answers only from the app guide", whoBn: "অ্যাপের সাহায্যকারী · শুধু অ্যাপ গাইড থেকে", en: "Sathi always shows the one next step, and helps with the app.", bn: "সাথী সবসময় পরের কাজটা দেখায়, অ্যাপ চালাতে সাহায্য করে।" },
  { ch: "Ask a person", chBn: "মানুষের কাছে", who: "Guard · the pharmacist replies, never the AI", whoBn: "গার্ড · উত্তর দেন ফার্মাসিস্ট, এআই নয়", en: "Medicine questions go to the pharmacist, never to the AI.", bn: "ওষুধের প্রশ্ন যায় ফার্মাসিস্টের কাছে, এআই-এর কাছে নয়।" },
  { ch: "Doctor visit", chBn: "ডাক্তার দেখানো", who: "One printable page", whoBn: "এক পাতায়, ছাপানো যায়", en: "Before every visit: what changed, and who changed it.", bn: "প্রতি ভিজিটের আগে: কী বদলেছে, আর কে বদলেছে।" },
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
  const t = useTranslations("demo");
  const isBn = useLocale() === "bn";
  // the chosen language leads; the other one is the accent line
  const lead = isBn ? { text: s.bn, lang: "bn", cls: "font-bn-display leading-[1.2]" } : { text: s.en, lang: "en", cls: "font-display leading-[1.04]" };
  const accent = isBn ? { text: s.en, lang: "en", cls: "font-display italic" } : { text: s.bn, lang: "bn", cls: "font-bn-display" };
  return (
      <div className="flex min-h-dvh flex-col overflow-x-clip">
        <JudgeBar />
        <div className={stickyBar}>
          <header className="mx-auto flex w-full max-w-[1680px] items-center justify-between gap-4 px-8 py-3 lg:px-16">
            <Wordmark />
            <div className="flex items-center gap-2">
              <DemoTag className="hidden sm:inline-flex" />
              <ThemeToggle className="h-11 w-11" />
              <LangToggle className="h-11" />
            </div>
          </header>
        </div>

        <main className="mx-auto grid w-full max-w-[1680px] flex-1 grid-cols-[minmax(0,1fr)] items-center gap-10 px-8 pb-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:gap-20 lg:px-16">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={`cap-${step}`}
              className="max-w-[720px]"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10, transition: { duration: 0.14 } }}
            >
              <p className="flex items-baseline gap-3 text-ink-faint">
                <span className="tabular font-display text-[30px] leading-none text-neel">{String(step + 1).padStart(2, "0")}</span>
                {isBn ? (
                  <span lang="bn" className="font-bn text-[17px] font-semibold">{s.chBn}</span>
                ) : (
                  <span className="text-[15px] font-semibold uppercase tracking-[0.14em]">{s.ch}</span>
                )}
              </p>
              <h1 lang={lead.lang} className={`mt-5 text-[clamp(38px,3.9vw,68px)] text-ink ${lead.cls}`}>{lead.text}</h1>
              <p lang={accent.lang} className={`mt-5 text-[clamp(22px,2vw,34px)] leading-snug text-ink-soft ${accent.cls}`}>{accent.text}</p>
              <span aria-hidden className="stitch-x mt-8 block w-28" />
              <p className="mt-4 inline-flex items-center gap-2 text-[16px] text-ink-soft">
                <span aria-hidden className="h-2 w-2 rounded-full bg-neel" /> {isBn ? s.whoBn : s.who}
              </p>
            </motion.div>
          </AnimatePresence>

          <div className="relative flex min-h-[520px] min-w-0 items-center justify-center text-[18px]">
            {/* the phone mock-ups are the family's screens, so they stay in Bangla */}
            <NextIntlClientProvider locale="bn" messages={bn} timeZone="Asia/Dhaka">
              <LayoutGroup id="demo">
                <Stage step={step} passportUrl={origin ? `${origin}/passport/1` : undefined} />
              </LayoutGroup>
            </NextIntlClientProvider>
          </div>
        </main>

        <footer className="mx-auto flex w-full max-w-[1680px] items-end justify-between gap-6 px-8 pb-6 lg:px-16">
          <ol className="grid min-w-0 flex-1 grid-cols-13 gap-2" aria-label={t("progress")}>
            {STEPS.map((st, i) => (
              <li key={i} className="min-w-0">
                <button
                  type="button"
                  aria-label={t("step", { n: i + 1, name: isBn ? st.chBn : st.ch })}
                  aria-current={i === step ? "step" : undefined}
                  onClick={() => setStep(i)}
                  className="group block w-full pt-2 text-left"
                >
                  <span className="relative block h-1">
                    <span className={cx("absolute inset-0 rounded-chip", i < step ? "stitch-x !h-[3px]" : "bg-rule")} />
                    {i === step && <motion.span layoutId="rail-active" className="absolute inset-0 rounded-chip bg-neel" />}
                  </span>
                  <span className={cx("mt-2 hidden truncate text-[13px] font-medium md:block", i === step ? "text-ink" : "text-ink-faint group-hover:text-ink-soft")}>{isBn ? st.chBn : st.ch}</span>
                </button>
              </li>
            ))}
          </ol>
          <div className="flex shrink-0 items-center gap-3 text-[15px] text-ink-faint">
            <span className="hidden items-center gap-2 lg:inline-flex"><Keyboard aria-hidden size={18} /> {t("keys")}</span>
            <button type="button" onClick={() => go(-1)} aria-label={t("back")} className="inline-flex h-12 w-12 items-center justify-center rounded-full border border-rule text-ink"><ArrowLeft aria-hidden size={18} /></button>
            <button type="button" onClick={() => go(1)} aria-label={t("next")} className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-neel text-on-neel"><ArrowRight aria-hidden size={18} /></button>
          </div>
        </footer>
      </div>
  );
}

/** True from the sm breakpoint up; false on the server and on phones. */
function useWide() {
  return useSyncExternalStore(
    (cb) => {
      const m = window.matchMedia("(min-width: 640px)");
      m.addEventListener("change", cb);
      return () => m.removeEventListener("change", cb);
    },
    () => window.matchMedia("(min-width: 640px)").matches,
    () => false,
  );
}

/** A strip that keeps its identity from step to step, so it travels instead of popping. */
function Card({ id, children, className, style, animate, delay = 0 }: {
  id: number; children: ReactNode; className?: string; style?: React.CSSProperties;
  animate?: { x?: number; y?: number; rotate?: number; opacity?: number }; delay?: number;
}) {
  return (
    <motion.div
      layoutId={`card-${id}`}
      className={className}
      style={style}
      initial={{ opacity: 0, y: (animate?.y ?? 0) + 24 }}
      animate={{ x: 0, y: 0, rotate: 0, opacity: 1, ...animate }}
      transition={{ ...SPRING_TRAVEL, delay }}
    >
      {children}
    </motion.div>
  );
}

/** Entrance for whole panels (dashboard, phone, passport, report). */
const panelIn = {
  initial: { opacity: 0, y: 28, scale: 0.98 },
  animate: { opacity: 1, y: 0, scale: 1 },
  transition: SPRING_TRAVEL,
};

/** A phone outline for screens the family sees. */
function Phone({ children, label }: { children: ReactNode; label: string }) {
  return (
    <motion.figure className="demo-fit w-full max-w-[420px]" {...panelIn}>
      <div className="rounded-[40px] border border-rule-strong bg-paper-sunk p-3 shadow-lift">
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
    </motion.figure>
  );
}

function Pair({ wide, label, compact, delay }: { wide: boolean; label: string; compact?: boolean; delay?: number }) {
  const density = compact || !wide ? "compact" : "comfortable";
  return (
    <DuplicateConnector orientation={wide ? "horizontal" : "vertical"} label={label} snap={false} delay={delay}>
      <Card id={DEMO_ITEMS.napa.id}><StripCard item={DEMO_ITEMS.napa} density={density} highlight="red" /></Card>
      <Card id={DEMO_ITEMS.ace.id}><StripCard item={DEMO_ITEMS.ace} density={density} highlight="red" /></Card>
    </DuplicateConnector>
  );
}

function Stage({ step, passportUrl }: { step: number; passportUrl?: string }) {
  const wide = useWide();
  if (step <= 1) {
    // the messy shelf: strips in a pile; step 2 adds the camera frame around it
    return (
      <div className="relative h-[480px] w-full max-w-[500px]">
        {SHELF.map((it, i) => (
          <Card
            key={it.id}
            id={it.id}
            delay={step === 0 ? i * 0.08 : 0}
            className="absolute left-1/2 top-[60px] -ml-[170px] w-[340px]"
            style={{ zIndex: i }}
            animate={{ x: PILE[i].x, y: PILE[i].y, rotate: PILE[i].r }}
          >
            <StripCard item={it} density="compact" />
          </Card>
        ))}
        {step === 1 && (
          <motion.div
            aria-hidden
            className="pointer-events-none absolute -inset-x-6 -inset-y-2 z-20 rounded-[28px]"
            initial={{ opacity: 0, scale: 1.08 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={SPRING_TRAVEL}
          >
            {/* kantha-stitched frame, solid corners */}
            <span className="absolute inset-0 rounded-[28px] border-2 border-dashed border-stitch" />
            {["left-0 top-0 border-l-4 border-t-4 rounded-tl-[28px]", "right-0 top-0 border-r-4 border-t-4 rounded-tr-[28px]", "bottom-0 left-0 border-b-4 border-l-4 rounded-bl-[28px]", "bottom-0 right-0 border-b-4 border-r-4 rounded-br-[28px]"].map((c) => (
              <span key={c} className={`absolute h-12 w-12 border-neel ${c}`} />
            ))}
            <motion.span
              className="absolute inset-x-8 top-6 h-[2px] rounded-chip bg-neel/70"
              initial={{ y: 0, opacity: 0 }}
              animate={{ y: [0, 400, 0], opacity: [0, 1, 0] }}
              transition={{ duration: 2.4, ease: "easeInOut", repeat: Infinity, repeatDelay: 0.4 }}
            />
            <span className="absolute -bottom-5 left-1/2 inline-flex h-10 -translate-x-1/2 items-center gap-2 rounded-chip bg-neel px-4 text-[15px] font-semibold text-on-neel shadow-soft">
              <Camera aria-hidden size={17} /> {SHELF.length} strips in view
            </span>
          </motion.div>
        )}
      </div>
    );
  }
  if (step === 2) {
    return (
      <div className="demo-fit-sm grid w-full max-w-[880px] gap-4 sm:grid-cols-2">
        {SHELF.map((it, i) => (
          <Card key={it.id} id={it.id} delay={i * 0.06}>
            <StripCard item={it} density="compact" />
          </Card>
        ))}
      </div>
    );
  }
  if (step === 3) {
    // the hero moment: the pair travels together, everything else steps back
    return (
      <div className="w-full max-w-[860px]">
        <Pair wide={wide} label="দুটোই প্যারাসিটামল" delay={350} />
        <motion.p
          lang="en"
          className="mt-5 text-center text-[17px] text-ink-soft"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...SPRING_TRAVEL, delay: 0.6 }}
        >
          From the <b className="font-semibold text-ink">local drug shop</b> and the <b className="font-semibold text-ink">village doctor</b>: two prescribers, one medicine.
        </motion.p>
        {wide && (
          <div aria-hidden className="mt-8 grid grid-cols-2 gap-4">
            {[DEMO_ITEMS.camlodin, comet].map((it) => (
              <Card key={it.id} id={it.id} animate={{ opacity: 0.4 }} className="saturate-50">
                <StripCard item={it} density="compact" />
              </Card>
            ))}
          </div>
        )}
      </div>
    );
  }
  if (step === 4) {
    return (
      <motion.div lang="en" className="demo-fit-sm w-full max-w-[720px] overflow-hidden rounded-card border border-rule-strong bg-paper-raised text-[15px] shadow-lift" {...panelIn}>
        <div className="flex items-center justify-between border-b border-rule bg-paper-sunk/60 px-6 py-3 text-[14px] text-ink-soft">
          <span className="inline-flex items-center gap-2 font-semibold text-ink"><Stethoscope aria-hidden size={17} /> Clinical review · queue</span>
          <span className="flex items-center gap-1.5">
            {["J", "K", "C", "D", "N"].map((k) => (
              <kbd key={k} className={cx("inline-flex h-6 min-w-6 items-center justify-center rounded border px-1.5 font-mono text-[12px]", k === "C" ? "border-neel bg-neel text-on-neel" : "border-rule-strong bg-paper-raised")}>{k}</kbd>
            ))}
          </span>
        </div>
        <div className="p-6">
          <div className="flex flex-wrap items-center gap-3">
            <SeverityBadge severity="red" label="Red · for the doctor" />
            <span className="font-display text-[28px] leading-none">Same generic, two brands</span>
          </div>
          <p className="mt-2 text-ink-soft">Rahima Begum, 68 · rule <code className="font-mono text-[14px]">DUPLICATE_GENERIC</code> · source: brand table</p>
          <motion.div {...later(0.15)} className="mt-4 rounded-card border border-dashed border-rule-strong bg-paper px-4 py-3 text-[14px]">
            <p className="flex items-center gap-2 font-semibold text-ink"><Sparkles aria-hidden size={15} className="text-neel" /> AI summary — check the evidence</p>
            <ul className="mt-1.5 grid list-disc gap-0.5 pl-5 text-ink-soft">
              <li>9 confirmed medicines from three prescribers.</li>
              <li>Napa and Ace both contain paracetamol.</li>
            </ul>
          </motion.div>
          <div className="mt-5"><Pair wide={wide} label="Both are paracetamol" compact delay={200} /></div>
          <p className="mt-5 font-semibold text-ink">Note to the family</p>
          <p className="mt-1.5 rounded-md border border-rule-strong bg-paper px-3.5 py-2.5 text-ink">{DEMO_FLAG.note}</p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <motion.span
              className="inline-flex h-12 items-center gap-2 rounded-card bg-neel px-5 font-semibold text-on-neel"
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ ...SPRING_TRAVEL, delay: 0.7 }}
            >
              <Check aria-hidden size={18} strokeWidth={2.5} /> Confirmed by Demo pharmacist
            </motion.span>
            <span className="text-ink-faint">Every decision is recorded with the reviewer&rsquo;s name.</span>
          </div>
        </div>
      </motion.div>
    );
  }
  if (step === 5) return <Phone label="ওষুধসাথী"><FlagResult flag={DEMO_FLAG} /></Phone>;
  if (step === 7) return <Phone label="ওষুধসাথী"><EmergencyScene /></Phone>;
  if (step === 8) return <Phone label="ওষুধসাথী"><TodayScene /></Phone>;
  if (step === 10) return <Phone label="ওষুধসাথী"><SathiGuideScene /></Phone>;
  if (step === 11) return <Phone label="ওষুধসাথী"><SathiHumanScene /></Phone>;
  if (step === 12) return <VisitScene />;
  if (step === 6)
    return (
      <motion.div className="demo-fit w-full max-w-[580px]" initial={{ opacity: 0, y: 40, rotate: -2 }} animate={{ opacity: 1, y: 0, rotate: 0.6 }} transition={SPRING_TRAVEL}>
        <MedicinePassport passport={DEMO_PASSPORT} url={passportUrl} />
      </motion.div>
    );
  const first = DEMO_BP[0];
  const last = DEMO_BP[DEMO_BP.length - 1];
  return (
    <motion.div className="w-full max-w-[640px] rounded-card border border-rule bg-paper-raised p-7 shadow-lift" {...panelIn}>
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <p className="font-bn-display text-[26px]">রক্তচাপ — গত ৭ দিন</p>
        {first && last && (
          <p lang="en" className="tabular text-[15px] text-ink-soft">
            {first.systolic}/{first.diastolic} → <b className="font-semibold text-ink">{last.systolic}/{last.diastolic}</b> mmHg
          </p>
        )}
      </div>
      <div className="mt-4"><BPTrend readings={DEMO_BP} height={300} /></div>
      <motion.p {...later(0.5)} className="mt-4 flex flex-wrap items-center gap-2 rounded-md border border-dashed border-rule-strong px-4 py-3 text-[15px] text-ink">
        <Camera aria-hidden size={18} className="text-neel" /> Read from a photo of the machine: <b className="tabular font-semibold">142/88</b>
        <span className="text-ink-soft">· the family checks it against the machine before saving</span>
      </motion.p>
      <p className="mt-4 border-t border-rule pt-4 text-[15px] text-ink-soft">Sent to the family every Friday. Target 140/90 marked on the chart.</p>
    </motion.div>
  );
}

const later = (delay: number) => ({
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  transition: { ...SPRING_TRAVEL, delay },
});

function Bubble({ children, delay }: { children: ReactNode; delay: number }) {
  return <motion.p {...later(delay)} className="ml-auto w-fit max-w-[85%] rounded-card bg-neel px-4 py-2.5 text-on-neel">{children}</motion.p>;
}

/** Scene: the next-step card, then a quick-reply chip answered from the app guide. */
function SathiGuideScene() {
  return (
    <div className="grid gap-4">
      <motion.section {...later(0.1)} className="rounded-card border border-neel/40 bg-paper-raised p-5 shadow-soft">
        <p className="flex items-center gap-2 text-[15px] font-semibold text-neel"><SathiMark size={24} /> পরের কাজ</p>
        <p className="mt-3 font-bn-display text-[24px] leading-[1.35] text-ink">৩টি ওষুধ আপনার যাচাইয়ের অপেক্ষায়।</p>
        <span className="mt-4 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-card border border-neel px-5 font-semibold text-neel">
          মিলিয়ে নিন <ArrowRight aria-hidden size={20} />
        </span>
      </motion.section>
      <motion.div {...later(0.6)} className="flex flex-wrap gap-2">
        {["কীভাবে ঠিক করব?", "ছবি ঝাপসা হলে?", "এটা কে দেখবেন?"].map((c, i) => (
          <span key={c} className={cx("rounded-chip border px-4 py-2 text-base font-medium", i === 1 ? "border-neel bg-neel text-on-neel" : "border-neel/50 bg-neel-tint text-ink")}>{c}</span>
        ))}
      </motion.div>
      <Bubble delay={1.1}>ছবি ঝাপসা হলে?</Bubble>
      <motion.div {...later(1.6)} className="max-w-[92%] rounded-card border border-rule bg-paper-raised p-4">
        <p className="mb-1.5 flex items-center gap-1.5 text-[14px] font-medium text-ink-soft"><BookOpen aria-hidden size={15} /> অ্যাপ গাইড থেকে</p>
        <p className="text-ink">ঝাপসা ছবি মুছে আবার তুলুন: ফোন স্থির রাখুন আর লেখার ওপর একবার ট্যাপ করে ফোকাস করুন।</p>
        <p className="mt-2 font-semibold text-neel underline underline-offset-4">এই পাতায় যান</p>
      </motion.div>
    </div>
  );
}

/** Scene: a medicine question is redirected to the pharmacist, and a person replies. */
function SathiHumanScene() {
  return (
    <div className="grid gap-4">
      <Bubble delay={0.1}>Ace কি বন্ধ করে দেব?</Bubble>
      <motion.div {...later(0.6)} className="max-w-[92%] rounded-card border border-amber-line bg-amber-tint/60 p-4">
        <p className="flex items-start gap-2 text-ink">
          <ShieldQuestion aria-hidden size={20} className="mt-1 shrink-0 text-amber" />
          <span>এই প্রশ্নের উত্তর ফার্মাসিস্ট বা ডাক্তার দেবেন। আমি আপনার প্রশ্নটা তাঁদের কাছে পাঠাতে পারি।</span>
        </p>
        <span className="mt-3 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-card bg-neel px-5 font-semibold text-on-neel">
          <Send aria-hidden size={18} /> ফার্মাসিস্টকে জিজ্ঞেস করুন
        </span>
      </motion.div>
      <motion.p {...later(1.3)} className="flex items-center gap-2 font-medium text-ink"><Check aria-hidden size={20} className="text-green" /> পাঠানো হয়েছে।</motion.p>
      <motion.div {...later(2.1)} className="rounded-md border-l-4 border-neel bg-neel-tint/60 p-4">
        <p className="flex items-center gap-2 text-[15px] font-semibold text-neel"><MessageSquareReply aria-hidden size={18} /> Demo pharmacist-এর উত্তর</p>
        <p className="mt-1.5 text-ink">দুটোতেই প্যারাসিটামল আছে। আমি ডাক্তারকে জানিয়েছি, পরের ভিজিটে তিনি ঠিক করে দেবেন।</p>
        <p lang="en" className="mt-2 text-[13px] text-ink-faint">Written by a person. The AI never answers medical questions.</p>
      </motion.div>
    </div>
  );
}

/** Scene: what the passport QR opens. Read-only, first name only, the family can switch it off. */
function EmergencyScene() {
  return (
    <div className="grid gap-4">
      <motion.p {...later(0.1)} className="flex items-center gap-2 rounded-md border-b-4 border-red bg-red-tint px-4 py-3 text-lg font-bold text-red">
        <ShieldAlert aria-hidden size={22} /> জরুরি চিকিৎসা তথ্য
      </motion.p>
      <motion.p {...later(0.3)} className="font-bn-display text-[26px]">রহিমা <span className="text-lg text-ink-soft">৬৮ বছর</span></motion.p>
      <motion.div {...later(0.6)} className="rounded-card border-2 border-red p-4">
        <p className="flex items-center gap-2 font-semibold text-red"><AlertTriangle aria-hidden size={18} /> অ্যালার্জি</p>
        <p className="mt-1 text-2xl font-bold">Penicillin</p>
      </motion.div>
      <motion.span {...later(0.9)} className="flex min-h-14 items-center gap-3 rounded-card bg-neel px-5 font-semibold text-on-neel">
        <PhoneIcon aria-hidden size={22} /> Nusrat (daughter)-কে ফোন করুন
      </motion.span>
      <motion.ul {...later(1.2)} className="grid gap-2">
        {[["Amlodipine", "Camlodin 5 mg", "সকাল"], ["Metformin", "Comet 500 mg", "সকাল · রাত"]].map(([g, b, w]) => (
          <li key={g} className="rounded-card border border-rule p-3"><b className="text-[19px]">{g}</b> <span className="text-ink-soft">{b}</span><span className="block text-[15px] text-ink-soft">{w}</span></li>
        ))}
      </motion.ul>
    </div>
  );
}

/** Scene: today's medicines for a parent who cannot read. */
function TodayScene() {
  const pills = (n: number) => (
    <span className="flex gap-1">{Array.from({ length: n }).map((_, i) => <span key={i} className="h-5 w-5 rounded-full border-2 border-ink bg-paper" />)}</span>
  );
  return (
    <div className="grid gap-3">
      <motion.div {...later(0.1)} className="flex items-center justify-between">
        <p className="font-bn-display text-[28px]">আজকের ওষুধ</p>
        <span className="inline-flex h-11 items-center gap-1.5 rounded-card bg-neel px-4 font-semibold text-on-neel"><Volume2 aria-hidden size={18} /> শুনুন</span>
      </motion.div>
      {([[Sunrise, "সকাল", "text-amber", [["Camlodin", 1], ["Comet", 1]]], [Sun, "দুপুর", "text-amber", [["Ace", 1]]], [Moon, "রাত", "text-neel", [["Comet", 1], ["Amdocal", 1]]]] as const).map(([Icon, label, tone, meds], i) => (
        <motion.section key={label} {...later(0.3 + i * 0.25)} className="rounded-card border border-rule p-4">
          <p className="flex items-center gap-3"><Icon aria-hidden size={40} strokeWidth={1.75} className={tone} /><span className="font-bn-display text-[24px]">{label}</span></p>
          <ul className="mt-2 grid gap-2">
            {meds.map(([m, n]) => (
              <li key={m} className="flex items-center gap-3"><span aria-hidden className="foil h-11 w-11 shrink-0 rounded-md border border-foil-lo" /><b className="flex-1 text-[18px]">{m}</b>{pills(n)}</li>
            ))}
          </ul>
        </motion.section>
      ))}
    </div>
  );
}

/** Scene: before the doctor visit, one printable page. */
function VisitScene() {
  return (
    <motion.div className="demo-fit-sm w-full max-w-[760px] rounded-card border border-rule-strong bg-paper-raised p-7 text-[16px] shadow-lift" {...panelIn}>
      <div className="flex items-center justify-between gap-3">
        <p className="font-bn-display text-[28px]">ডাক্তারের কাছে যাওয়ার আগে</p>
        <span className="inline-flex h-10 items-center gap-1.5 rounded-card border border-rule-strong px-3 text-[14px] font-semibold"><Printer aria-hidden size={16} /> Print</span>
      </div>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <motion.div {...later(0.3)} className="rounded-md border border-rule p-4">
          <p className="font-semibold">What changed since the last visit</p>
          <p className="mt-2 flex items-center gap-2"><Minus aria-hidden size={16} className="text-red" /> <b>Ace</b> stopped <span className="text-ink-soft">· Demo pharmacist</span></p>
          <p className="mt-1 flex items-center gap-2"><Plus aria-hidden size={16} className="text-green" /> <b>Comet</b> added <span className="text-ink-soft">· Dr. A</span></p>
        </motion.div>
        <motion.div {...later(0.6)} className="rounded-md border border-rule p-4">
          <p className="font-semibold">Our questions for the doctor</p>
          <ol className="mt-2 grid list-decimal gap-1 pl-5" lang="bn"><li>প্রেশারের ওষুধ কি একটা কমানো যায়?</li><li>রাতে ঘুমের ওষুধ কি দরকার?</li></ol>
        </motion.div>
        <motion.div {...later(0.9)} className="rounded-md border border-rule p-4 sm:col-span-2">
          <p className="font-semibold">Blood pressure, last 4 weeks</p>
          <div className="mt-2"><BPTrend readings={DEMO_BP} height={170} /></div>
        </motion.div>
      </div>
      <motion.span {...later(1.2)} className="mt-5 inline-flex min-h-12 items-center gap-2 rounded-card bg-neel px-5 font-semibold text-on-neel">
        <Camera aria-hidden size={18} /> Visit done: scan the new prescription
      </motion.span>
    </motion.div>
  );
}
