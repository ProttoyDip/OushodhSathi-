import { ArrowRight, BookOpen, ExternalLink, ShieldCheck, Stethoscope } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { NextIntlClientProvider } from "next-intl";
import en from "../../messages/en.json";
import { Wordmark } from "@/components/BrandMark";
import { HeroDemo } from "@/components/landing/HeroDemo";
import { FlowStrip } from "@/components/landing/FlowStrip";

export const metadata: Metadata = {
  title: "OushodhSathi · ওষুধসাথী — a pharmacist for every elderly home in Bangladesh",
};

const EVIDENCE = [
  {
    figure: "78 per 1,000",
    claim: "Hypertension is now the most common illness in Bangladesh.",
    source: "BBS Health and Morbidity Status Survey (HMSS) 2025, reported by BSS",
    href: "https://www.bssnews.net/others/337437",
  },
  {
    figure: "11%",
    claim: "of people with hypertension in Bangladesh had their blood pressure under control (below 140/90).",
    source: "Background figure in the WHO-HEARTS evaluation, Heart (BMJ), 2024",
    href: "https://heart.bmj.com/content/heartjnl/early/2024/07/16/heartjnl-2024-324253.full.pdf",
  },
  {
    figure: "69%",
    claim: "of geriatric outpatients were prescribed five or more medicines.",
    source: "Small 2011 study of 35 patients at a private hospital in Bangladesh",
    href: "https://www.academia.edu/111376182/Trends_of_prescribing_for_out_door_geriatric_patients_in_a_private_hospital_of_Bangladesh",
  },
];

const SAFETY = [
  ["Rules make every finding.", "A deterministic engine flags duplicates, interactions, drugs risky after 65 and expired strips. Language models never create, remove or grade a finding."],
  ["A clinician confirms before the family sees it.", "Findings start as pending. The API only ever returns confirmed findings to the family, and a test enforces it."],
  ["We never tell anyone to stop a medicine.", "Explanations are checked for doses and stop-words, and always end: ডাক্তারের সাথে কথা না বলে কোনো ওষুধ বন্ধ বা পরিবর্তন করবেন না।"],
  ["Uncertain readings are marked.", "Anything read with under 75% confidence, or matched from the web, is shown as needing a human check."],
  ["Names stay out of models.", "Only medicine photos and medicine names reach a model. Patient names and phone numbers never do."],
  ["Photos are not kept.", "Photos are read in memory and discarded; the family sees a thumbnail once."],
];

export default function Landing() {
  return (
    <NextIntlClientProvider locale="en" messages={en} timeZone="Asia/Dhaka">
      <div lang="en" className="min-h-dvh">
        <nav aria-label="Main" className="mx-auto flex max-w-[1200px] items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <Link href="/" aria-label="OushodhSathi home"><Wordmark /></Link>
          <div className="flex items-center gap-1 sm:gap-2">
            <a href="#how" className="hidden h-11 items-center rounded-chip px-3 text-[15px] font-medium text-ink-soft hover:text-ink md:inline-flex">How it works</a>
            <a href="#safe" className="hidden h-11 items-center rounded-chip px-3 text-[15px] font-medium text-ink-soft hover:text-ink md:inline-flex">Why it&rsquo;s safe</a>
            <Link href="/docs" className="hidden h-11 items-center rounded-chip px-3 text-[15px] font-medium text-ink-soft hover:text-ink sm:inline-flex">Docs</Link>
            <Link href="/review" className="inline-flex h-11 items-center gap-1.5 rounded-chip border border-rule px-4 text-[15px] font-medium text-ink hover:border-rule-strong">
              <Stethoscope aria-hidden size={16} /> Reviewer
            </Link>
          </div>
        </nav>

        {/* first viewport: the mechanism itself */}
        <header className="mx-auto grid max-w-[1200px] grid-cols-[minmax(0,1fr)] items-center gap-12 px-5 pb-16 pt-8 sm:px-8 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:pb-24 lg:pt-14">
          <div className="min-w-0">
            <h1 className="font-display text-[clamp(42px,5.6vw,76px)] leading-[1.0] text-ink">
              Napa and Ace are <br className="hidden sm:block" />the same&nbsp;medicine.
            </h1>
            <p lang="bn" className="mt-4 font-bn-display text-[clamp(22px,2.4vw,28px)] leading-snug text-ink-soft">
              নাম আলাদা, ওষুধ একই — প্যারাসিটামল, দুইবার।
            </p>
            <p className="mt-6 max-w-[54ch] text-lg leading-relaxed text-ink-soft">
              Elderly Bangladeshis collect medicines from a hospital doctor, a village doctor and the local drug shop,
              under thousands of brand names, and nobody looks at the whole shelf. OushodhSathi reads every strip in the
              house, catches duplicates and dangerous combinations, and a pharmacist or doctor confirms every finding
              before the family sees it, in simple Bangla.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link href="/p/1" className="inline-flex min-h-14 items-center gap-2.5 rounded-card bg-neel px-7 text-lg font-semibold text-on-neel shadow-soft transition-colors hover:bg-neel-hover">
                See the demo <ArrowRight aria-hidden size={20} />
              </Link>
              <Link href="/review" className="inline-flex min-h-14 items-center gap-2 rounded-card border border-rule-strong bg-paper-raised px-6 text-lg font-semibold text-ink hover:border-ink-faint">
                Reviewer dashboard
              </Link>
            </div>
            <p className="mt-4 text-[15px] text-ink-faint">The demo opens the invented household of Rahima Begum, 68, Cumilla.</p>
          </div>
          <div className="dyed-cloth px-5 pb-6 pt-8 sm:px-8 sm:pb-8 sm:pt-10">
            <HeroDemo />
          </div>
        </header>

        {/* how it works */}
        <section id="how" aria-labelledby="how-h" className="border-y border-rule bg-paper-raised">
          <div className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8">
            <h2 id="how-h" className="font-display text-[clamp(36px,4.4vw,56px)] leading-none">How it works</h2>
            <p lang="bn" className="mt-2 font-bn-display text-[22px] text-ink-soft">ছবি থেকে নিশ্চিত তালিকা</p>
            <span aria-hidden className="stitch-x mt-6 block w-24" />
            <p className="mt-5 max-w-[62ch] text-lg text-ink-soft">
              A family member photographs every strip, box and prescription. Six steps later the family has one
              clinician-checked list and a passport to carry to every doctor visit.
            </p>
            <FlowStrip />
          </div>
        </section>

        {/* why it's safe */}
        <section id="safe" aria-labelledby="safe-h" className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8">
          <div className="grid grid-cols-[minmax(0,1fr)] gap-12 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <div>
              <h2 id="safe-h" className="font-display text-[clamp(36px,4.4vw,56px)] leading-[1.02]">
                AI for perception. Rules and humans for judgement.
              </h2>
              <p lang="bn" className="mt-3 font-bn-display text-[22px] text-ink-soft">এআই পড়ে, নিয়ম আর মানুষ বিচার করে।</p>
              <span aria-hidden className="stitch-x mt-6 block w-24" />
              <p className="mt-6 max-w-[48ch] text-lg text-ink-soft">
                A vision model is good at reading a cut strip under a tube light. It is not who should decide that a
                68-year-old is taking paracetamol twice. So it doesn&rsquo;t.
              </p>
            </div>
            <ol className="grid gap-0 border-t border-rule">
              {SAFETY.map(([title, body]) => (
                <li key={title} className="grid grid-cols-[28px_1fr] gap-4 border-b border-rule py-5">
                  <ShieldCheck aria-hidden size={22} className="mt-0.5 text-neel" />
                  <div>
                    <p className="text-lg font-semibold text-ink">{title}</p>
                    <p className="mt-1 text-ink-soft">{body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* evidence */}
        <section aria-labelledby="ev-h" className="bg-ink text-paper">
          <div className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8">
            <h2 id="ev-h" className="max-w-[24ch] font-display text-[clamp(32px,3.8vw,48px)] leading-[1.05]">
              The shelf problem, in public numbers.
            </h2>
            <div className="mt-12 grid gap-10 md:grid-cols-3">
              {EVIDENCE.map((e) => (
                <figure key={e.figure} className="border-t border-paper/25 pt-5">
                  <p className="tabular font-display text-[56px] leading-none">{e.figure}</p>
                  <p className="mt-3 text-lg leading-snug opacity-90">{e.claim}</p>
                  <figcaption className="mt-3 text-[15px] opacity-75">
                    <a href={e.href} target="_blank" rel="noreferrer" className="inline-flex items-start gap-1 underline">
                      {e.source} <ExternalLink aria-hidden size={13} className="mt-1 shrink-0" />
                    </a>
                  </figcaption>
                </figure>
              ))}
            </div>
            <p className="mt-12 max-w-[70ch] text-[15px] opacity-75">
              Pilot in progress. We will publish results here only once they are real; nothing on this site is a pilot
              outcome.
            </p>
          </div>
        </section>

        {/* team */}
        <section aria-labelledby="team-h" className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8">
          <h2 id="team-h" className="font-display text-[clamp(32px,3.8vw,48px)] leading-none">Team</h2>
          <p className="mt-3 text-ink-soft">Built for the International AI Builders Congress 2026 · HealthSphere AI → ChronicCare AI.</p>
          <ul className="mt-8 grid gap-4 sm:grid-cols-3">
            {["Team member 1", "Team member 2", "Team member 3"].map((n) => (
              <li key={n} className="rounded-card border border-dashed border-rule-strong p-5">
                <p className="font-semibold text-ink-soft">[{n} — name to be added]</p>
                <p className="text-[15px] text-ink-faint">[Role] · [GitHub]</p>
              </li>
            ))}
          </ul>
        </section>

        <footer className="border-t border-rule">
          <div className="mx-auto flex max-w-[1200px] flex-wrap items-start justify-between gap-6 px-5 py-10 sm:px-8">
            <div className="max-w-[60ch]">
              <Wordmark />
              <p className="mt-3 text-[15px] text-ink-soft">
                OushodhSathi is a research prototype, not a medical device. It does not give medical advice. All findings
                must be confirmed by a registered pharmacist or doctor. Demo data is invented.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link href="/docs" className="inline-flex h-11 items-center gap-1.5 rounded-chip border border-rule px-4 text-[15px] font-medium"><BookOpen aria-hidden size={16} /> Technical docs</Link>
              <Link href="/styleguide" className="inline-flex h-11 items-center rounded-chip border border-rule px-4 text-[15px] font-medium">Design system</Link>
            </div>
          </div>
        </footer>
      </div>
    </NextIntlClientProvider>
  );
}
