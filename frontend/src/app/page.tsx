/* Hallmark · genre: editorial (clinical) · macrostructure: Split Studio · design-system: DESIGN.md (Neel)
 * nav: sticky bar (N1b-like, kept) · footer: Ft3 columns (kept: a real hub of 13 destinations)
 * enrichment: live product (real StripCards on the dyed cloth) · no drawn device chrome
 * pre-emit critique: P5 H4 E4 S5 R5 V4
 */
import {
  ArrowRight, BookOpen, CirclePlay, Keyboard, ListOrdered, MessageCircle, Phone, Route, ExternalLink, ImageOff, Languages, Plus, ShieldCheck, Stethoscope,
} from "lucide-react";
import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import { Analytics } from "@vercel/analytics/next";
import { Wordmark } from "@/components/BrandMark";
import { LangToggle, ThemeToggle } from "@/components/Chrome";
import { MotionToggle } from "@/components/MotionToggle";
import { WarmUp } from "@/components/JudgeBar";
import { BrandMarquee } from "@/components/landing/BrandMarquee";
import facts from "@/data/brandFacts.json";
import ev from "@/data/evidence.json";
import { HowStory } from "@/components/landing/HowStory";
import { storyVisuals } from "@/components/landing/StoryVisuals";
import { ProductFrames, ReviewScreenshot } from "@/components/landing/ProductFrames";
import { stickyBar } from "@/lib/layout";
import { demoHref, GITHUB_URL, VIDEO_URL } from "@/lib/site";
import { TEAM } from "@/lib/team";

export const metadata: Metadata = {
  title: "OushodhSathi · ওষুধসাথী — a pharmacist for every elderly home in Bangladesh",
};

const EVIDENCE = [
  { key: "e1", href: "https://www.bssnews.net/others/337437" },
  { key: "e2", href: "https://heart.bmj.com/content/heartjnl/early/2024/07/16/heartjnl-2024-324253.full.pdf" },
  { key: "e3", href: "https://www.academia.edu/111376182/Trends_of_prescribing_for_out_door_geriatric_patients_in_a_private_hospital_of_Bangladesh" },
] as const;

const FAQ = ["q1", "q2", "q3", "q4", "q5", "q6"] as const;
const RULE_ITEMS = ["dup", "cls", "int", "beers", "acb", "look", "tw", "kid", "kt", "abx", "exp"] as const;
const PROMISES = ["r3", "r4", "r5", "r6"] as const;
const STEPS = [
  { key: "s1", actor: "family" }, { key: "s2", actor: "ai" }, { key: "s3", actor: "rules" },
  { key: "s4", actor: "rules" }, { key: "s5", actor: "human" }, { key: "s6", actor: "family" },
] as const;

// The check-in texts exactly as backend/app/whatsapp_checkin/flow.py and voice_calls/script.py send them.
const WA_MESSAGE = "আসসালামু আলাইকুম, ওষুধসাথী থেকে বলছি। আজকের ওষুধগুলো কি খাওয়া হয়েছে?";
const WA_BUTTONS = ["সব খেয়েছি", "কিছু বাদ গেছে", "জরুরি সমস্যা"] as const;
const CALL_PROMPT = "সকালের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন।";
const KEYPAD = ["১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯"] as const;

const sectionTitle = "font-display text-[clamp(34px,4.2vw,54px)] leading-[1.06] text-ink [overflow-wrap:anywhere]";
const navLink = "hidden h-11 items-center whitespace-nowrap rounded-chip px-3 text-[15px] font-medium text-ink-soft hover:text-ink";
const primaryBtn = "press inline-flex min-h-14 items-center justify-center gap-2.5 whitespace-nowrap rounded-card bg-neel px-6 text-[17px] font-semibold text-on-neel shadow-soft transition-colors hover:bg-neel-hover sm:px-7 sm:text-lg";
const secondaryBtn = "press inline-flex min-h-14 items-center justify-center gap-2 whitespace-nowrap rounded-card border border-rule-strong bg-paper-raised px-6 text-[17px] font-semibold text-ink transition-colors hover:border-ink-faint sm:text-lg";

export default async function Landing() {
  const t = await getTranslations("landing");
  const locale = await getLocale();
  // The accent line under each heading is always in the other language. Roman, never italic.
  const accentLang = locale === "bn" ? "en" : "bn";
  const accent = locale === "bn" ? "font-display font-medium" : "font-bn-display";
  const demo = demoHref("/p/1");
  const visuals = await storyVisuals();

  return (
    <div className="landing landing-light min-h-dvh overflow-x-clip">
      <WarmUp />
      <Analytics />
      <div className={stickyBar}>
        <nav aria-label="Main" className="mx-auto flex max-w-[1200px] items-center justify-between gap-3 px-5 py-3 sm:px-8">
          <Link href="/" title={t("nav.home")} className="shrink-0"><Wordmark /></Link>
          <div className="flex items-center gap-1 sm:gap-2">
            <a href="#how" className={`${navLink} lg:inline-flex`}>{t("nav.how")}</a>
            <a href="#safe" className={`${navLink} lg:inline-flex`}>{t("nav.safe")}</a>
            <a href="#pharmacists" className={`${navLink} 2xl:inline-flex`}>{t("nav.pharm")}</a>
            <a href="#faq" className={`${navLink} lg:inline-flex`}>{t("nav.faq")}</a>
            <Link href="/docs" className={`${navLink} md:inline-flex`}>{t("nav.docs")}</Link>
            <Link href="/review" className="hidden h-11 items-center gap-1.5 whitespace-nowrap rounded-chip border border-rule px-4 text-[15px] font-medium text-ink hover:border-rule-strong sm:inline-flex">
              <Stethoscope aria-hidden size={16} /> {t("nav.reviewer")}
            </Link>
            <MotionToggle className="h-11" />
            <ThemeToggle className="h-11 w-11" />
            <LangToggle className="h-11" />
          </div>
        </nav>
      </div>

      {/* hero: the claim on one side, the product proving it on the other */}
      <header className="mx-auto max-w-[1200px] px-5 pb-14 pt-10 sm:px-8 lg:pb-20 lg:pt-16">
        {/* phones: claim, then the product, then the rest; desktop: claim and rest left, product right */}
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:grid-rows-[auto_1fr] lg:gap-x-16 lg:gap-y-0">
          <div className="min-w-0 lg:col-start-1 lg:row-start-1">
            <h1 className="font-display text-[clamp(42px,5.6vw,76px)] leading-[1.05] text-ink [overflow-wrap:anywhere]">
              <span>{t("hero.title1")}</span> <br className="hidden sm:block" />
              <span>{t("hero.title2")}</span>
            </h1>
            <p lang={accentLang} className={`mt-4 text-[clamp(20px,2.1vw,26px)] leading-snug text-neel ${accent}`}>
              {t("hero.accent")}
            </p>
          </div>
          <div className="min-w-0 lg:col-start-2 lg:row-span-2 lg:row-start-1 lg:self-center">
            <ProductFrames replayLabel={t("hero.replay")} phoneLabel={t("hero.framePhone")} />
          </div>
          <div className="min-w-0 lg:col-start-1 lg:row-start-2">
            <span aria-hidden className="stitch-x mt-7 block w-24 max-lg:hidden" />
            <p className="max-w-[56ch] text-lg leading-relaxed text-ink-soft lg:mt-7">{t("hero.body")}</p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Link href={demo} className={primaryBtn}>{t("hero.ctaDemo")} <ArrowRight aria-hidden size={20} /></Link>
              <Link href="/start" className={secondaryBtn}>{t("hero.ctaStart")}</Link>
            </div>
            <p className="mt-3 text-[15px] text-ink-faint">{t("hero.demoNote")}</p>
            <a href={VIDEO_URL} target="_blank" rel="noreferrer"
              className="mt-4 inline-flex min-h-11 items-center gap-2 whitespace-nowrap text-[16px] font-semibold text-neel underline-offset-4 hover:underline">
              <CirclePlay aria-hidden size={20} /> {t("hero.video")}
            </a>
            <ul className="mt-10 grid gap-3 border-t border-rule pt-6 text-[16px] font-medium text-ink-soft">
              {([["trust1", ShieldCheck], ["trust2", Languages], ["trust3", ImageOff]] as const).map(([k, Icon]) => (
                <li key={k} className="flex items-center gap-3"><Icon aria-hidden size={19} className="shrink-0 text-neel" /> {t(`hero.${k}`)}</li>
              ))}
            </ul>
          </div>
        </div>
      </header>

      <BrandMarquee locale={locale} title={t("names.title")} sr={t("names.sr")} pause={t("names.pause")} play={t("names.play")}
        caption={t("names.caption", { brands: facts.seedBrands, generics: facts.seedGenerics, shared: facts.seedSharedGenerics, dataset: facts.datasetBrands })} />

      {/* how it works: six steps, each shown with the real product; a sticky stage on desktop when motion is on */}
      <section id="how" aria-labelledby="how-h" className="scroll-mt-20 border-y border-rule bg-paper py-[var(--section-y)]">
        <div className="mx-auto max-w-[1200px] px-5 sm:px-8">
          <div className="max-w-[60ch]">
            <h2 id="how-h" className={sectionTitle}>{t("how.title")}</h2>
            <p lang={accentLang} className={`mt-3 text-[22px] text-neel ${accent}`}>{t("how.accent")}</p>
            <p className="mt-5 text-lg text-ink-soft">{t("how.body")}</p>
          </div>
          <div className="mt-12">
            <HowStory steps={STEPS.map(({ key, actor }, i) => ({
              key, actor, title: t(`flow.${key}.title`), alt: t(`flow.${key}.alt`), altLang: accentLang,
              body: t(`flow.${key}.body`), actorLabel: t(`flow.actor.${actor}`), srStep: t("how.step", { n: i + 1 }),
            }))} visuals={visuals} num={STEPS.map((_, i) => (i + 1).toLocaleString(locale === "bn" ? "bn-BD" : "en"))} />
          </div>
        </div>
      </section>

      {/* the one deep-indigo band: every rule that runs, with its source, then the promises that bound the AI */}
      <section id="safe" aria-labelledby="safe-h" className="dyed-band scroll-mt-20 py-[var(--section-y)]">
        <div className="mx-auto max-w-[1200px] px-5 sm:px-8">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:items-end">
            <div className="min-w-0">
              <h2 id="safe-h" className="font-display text-[clamp(34px,4.2vw,54px)] leading-[1.06] text-[#f3f5f9] [overflow-wrap:anywhere]">{t("rules.title")}</h2>
              <p lang={accentLang} className={`mt-3 text-[22px] text-[#c9d0f0] ${accent}`}>{t("rules.accent")}</p>
            </div>
            <p className="max-w-[52ch] text-lg leading-relaxed text-[#dfe3f5]">{t("rules.body")}</p>
          </div>
          <ul className="mt-12 grid gap-px overflow-hidden rounded-card border border-white/15 bg-white/15 sm:grid-cols-2 lg:grid-cols-3">
            {RULE_ITEMS.map((k) => (
              <li key={k} className="min-w-0 bg-[var(--dye-deep)] p-5">
                <h3 className="text-[19px] font-semibold leading-snug text-[#f3f5f9]">{t(`rules.items.${k}.name`)}</h3>
                <p className="mt-1.5 text-[15px] leading-relaxed text-[#c9d0f0]">
                  <span className="sr-only">{t("rules.sourceLabel")}: </span>{t(`rules.items.${k}.source`)}
                </p>
              </li>
            ))}
            <li className="min-w-0 bg-[var(--dye-deep)]">
              <Link href="/docs" className="flex h-full min-h-24 flex-col justify-center gap-1.5 p-5 text-[#f3f5f9] transition-colors hover:bg-white/5">
                <span className="inline-flex items-center gap-2 text-[19px] font-semibold"><BookOpen aria-hidden size={19} /> {t("safe.docsTitle")} <ArrowRight aria-hidden size={18} /></span>
                <span className="text-[15px] leading-relaxed text-[#c9d0f0]">{t("safe.docsBody")}</span>
              </Link>
            </li>
          </ul>
          <h3 className="mt-14 text-[21px] font-semibold text-[#f3f5f9]">{t("rules.promises")}</h3>
          <ul className="mt-5 grid gap-x-10 gap-y-6 md:grid-cols-2">
            {PROMISES.map((k) => (
              <li key={k} className="min-w-0 border-t border-white/20 pt-4">
                <p className="text-[18px] font-semibold leading-snug text-[#f3f5f9]">{t(`safe.${k}.title`)}</p>
                <p className="mt-1.5 max-w-[56ch] text-[16px] leading-relaxed text-[#dfe3f5]">{t(`safe.${k}.body`)}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* for pharmacists: the real reviewer screen and three things it does */}
      <section id="pharmacists" aria-labelledby="pharm-h" className="scroll-mt-20 bg-paper-raised py-[var(--section-y)]">
        <div className="mx-auto grid max-w-[1200px] gap-12 px-5 sm:px-8 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)] lg:items-center lg:gap-16">
          <div className="order-2 min-w-0 lg:order-1">
            <ReviewScreenshot label={t("hero.frameReview")} />
          </div>
          <div className="order-1 min-w-0 lg:order-2">
            <h2 id="pharm-h" className={sectionTitle}>{t("pharm.title")}</h2>
            <p lang={accentLang} className={`mt-3 text-[22px] text-neel ${accent}`}>{t("pharm.accent")}</p>
            <p className="mt-5 text-lg text-ink-soft">{t("pharm.body")}</p>
            <ol className="mt-8 grid gap-6">
              {([["c1", ListOrdered], ["c2", Route], ["c3", Keyboard]] as const).map(([k, Icon]) => (
                <li key={k} className="grid grid-cols-[28px_minmax(0,1fr)] gap-x-3">
                  <Icon aria-hidden size={22} className="mt-0.5 text-neel" />
                  <div className="min-w-0">
                    <h3 className="text-[19px] font-semibold leading-snug text-ink">{t(`pharm.${k}.title`)}</h3>
                    <p className="mt-1 text-[16px] leading-relaxed text-ink-soft">{t(`pharm.${k}.body`)}</p>
                  </div>
                </li>
              ))}
            </ol>
            <Link href="/review" className={`${secondaryBtn} mt-8`}><Stethoscope aria-hidden size={19} /> {t("pharm.cta")}</Link>
          </div>
        </div>
      </section>

      {/* daily follow-up: the WhatsApp message and the keypad call, as the family receives them (Bangla) */}
      <section aria-labelledby="follow-h" className="border-t border-rule bg-paper py-[var(--section-y)]">
        <div className="mx-auto max-w-[1200px] px-5 sm:px-8">
          <div className="max-w-[60ch]">
            <h2 id="follow-h" className={sectionTitle}>{t("follow.title")}</h2>
            <p lang={accentLang} className={`mt-3 text-[22px] text-neel ${accent}`}>{t("follow.accent")}</p>
            <p className="mt-5 text-lg text-ink-soft">{t("follow.body")}</p>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-2">
            <figure className="min-w-0 rounded-[20px] border border-rule-strong bg-paper-raised p-5 shadow-soft">
              <figcaption className="inline-flex items-center gap-2 text-[15px] font-semibold text-ink-soft"><MessageCircle aria-hidden size={17} /> {t("follow.wa")}</figcaption>
              <div lang="bn" className="mt-4 max-w-[340px] rounded-card rounded-tl-none border border-rule bg-paper p-4 text-[17px] leading-[1.7] text-ink">
                {WA_MESSAGE}
              </div>
              <ul lang="bn" className="mt-2 grid max-w-[340px] gap-2">
                {WA_BUTTONS.map((b) => (
                  <li key={b} className="rounded-card border border-rule bg-paper py-2.5 text-center text-[16px] font-semibold text-neel">{b}</li>
                ))}
              </ul>
            </figure>
            <figure className="min-w-0 rounded-[20px] border border-rule-strong bg-paper-raised p-5 shadow-soft">
              <figcaption className="inline-flex items-center gap-2 text-[15px] font-semibold text-ink-soft"><Phone aria-hidden size={17} /> {t("follow.call")}</figcaption>
              <p lang="bn" className="mt-4 text-[17px] leading-[1.7] text-ink">{CALL_PROMPT}</p>
              <div aria-hidden className="mt-4 grid max-w-[240px] grid-cols-3 gap-2">
                {KEYPAD.map((d) => (
                  <span key={d} className={`grid h-12 place-items-center rounded-full border text-[19px] font-semibold ${
                    d === "১" || d === "২" ? "border-neel text-neel" : d === "৯" ? "border-red text-red" : "border-rule text-ink-faint"}`}>{d}</span>
                ))}
              </div>
              <p lang="bn" className="mt-4 text-[16px] font-semibold text-ink-soft">{t("follow.keys")}</p>
            </figure>
          </div>
          <p className="mt-6 max-w-[70ch] text-[15px] text-ink-faint">{t("follow.note")}</p>
        </div>
      </section>

      {/* measured results: real photos first, from the results files in eval/ (frontend/src/data/evidence.json) */}
      <section aria-labelledby="measured-h" className="border-t border-rule bg-paper-raised py-[var(--section-y)]">
        <div className="mx-auto max-w-[1200px] px-5 sm:px-8">
          <h2 id="measured-h" className={sectionTitle}>{t("measured.title")}</h2>
          <p lang={accentLang} className={`mt-3 text-[22px] text-neel ${accent}`}>{t("measured.accent")}</p>
          <div className="mt-12 grid gap-12 md:grid-cols-3 md:gap-10">
            <figure className="min-w-0 border-t-2 border-neel pt-6">
              <p className="tabular font-display text-[clamp(56px,5.4vw,80px)] leading-none text-neel">{t("measured.photosFigure", { pct: ev.realBrand.pct })}</p>
              <p className="mt-5 text-lg leading-snug text-ink">{t("measured.photosClaim", ev.realBrand)}</p>
              <p className="mt-3 text-[16px] text-ink-soft">{t("measured.strength", { ...ev.realStrength, ck: ev.realClear.k, cn: ev.realClear.n })}</p>
              <p className="mt-3 text-[16px] font-semibold text-amber">{t("measured.weak", ev.realBangla)}</p>
            </figure>
            <figure className="min-w-0 border-t-2 border-neel pt-6">
              <p className="tabular font-display text-[clamp(56px,5.4vw,80px)] leading-none text-neel">{t("measured.sathiFigure", ev.sathiMedical)}</p>
              <p className="mt-5 text-lg leading-snug text-ink">{t("measured.sathiClaim", { ek: ev.sathiEmergency.k, en: ev.sathiEmergency.n })}</p>
            </figure>
            <figure className="min-w-0 border-t-2 border-neel pt-6">
              <p className="tabular font-display text-[clamp(56px,5.4vw,80px)] leading-none text-neel">{t("measured.retrFigure", ev.retrieval)}</p>
              <p className="mt-5 text-lg leading-snug text-ink">{t("measured.retrClaim", ev.retrieval)}</p>
            </figure>
          </div>
          <p className="mt-12 max-w-[75ch] text-[15px] text-ink-faint">{t("measured.note", { sk: ev.syntheticBrand.k, sn: ev.syntheticBrand.n })}</p>
          <Link href="/docs" className="mt-4 inline-flex min-h-12 items-center gap-2 text-[16px] font-semibold text-neel underline-offset-4 hover:underline">
            {t("measured.docs")} <ArrowRight aria-hidden size={17} />
          </Link>
        </div>
      </section>

      {/* evidence: the one full-width break in the diptych rhythm. Public numbers, each with its source */}
      <section aria-labelledby="ev-h" className="border-y border-rule bg-paper-raised">
        <div className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8 lg:py-24">
          <h2 id="ev-h" className="max-w-[22ch] font-display text-[clamp(32px,3.8vw,48px)] leading-[1.08] text-ink [overflow-wrap:anywhere]">
            {t("evidence.title")}
          </h2>
          <div className="mt-14 grid gap-12 md:grid-cols-3 md:gap-10">
            {EVIDENCE.map((e) => (
              <figure key={e.key} className="min-w-0 border-t-2 border-neel pt-6">
                <p className="flex flex-wrap items-baseline gap-x-3">
                  <span className="tabular font-display text-[clamp(56px,5.4vw,80px)] leading-none text-neel">{t(`evidence.${e.key}.figure`)}</span>
                  {t(`evidence.${e.key}.unit`) && <span className="text-lg font-semibold text-ink">{t(`evidence.${e.key}.unit`)}</span>}
                </p>
                <p className="mt-5 text-lg leading-snug text-ink">{t(`evidence.${e.key}.claim`)}</p>
                <figcaption className="mt-4 text-[15px] text-ink-faint">
                  <a href={e.href} target="_blank" rel="noreferrer" className="inline-flex items-start gap-1 underline underline-offset-4 hover:text-ink">
                    {t(`evidence.${e.key}.source`)} <ExternalLink aria-hidden size={13} className="mt-1 shrink-0" />
                  </a>
                </figcaption>
              </figure>
            ))}
          </div>
          <p className="mt-14 max-w-[70ch] text-[15px] text-ink-faint">{t("evidence.pilot")}</p>
        </div>
      </section>

      {/* questions families ask */}
      <section id="faq" aria-labelledby="faq-h" className="mx-auto max-w-[1200px] scroll-mt-20 px-5 py-20 sm:px-8 lg:py-24">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
          <div className="min-w-0">
            <h2 id="faq-h" className={sectionTitle}>{t("faq.title")}</h2>
            <p lang={accentLang} className={`mt-3 text-[22px] text-neel ${accent}`}>{t("faq.accent")}</p>
            <span aria-hidden className="stitch-x mt-6 block w-24" />
          </div>
          <div className="min-w-0 divide-y divide-rule border-y border-rule">
            {FAQ.map((k) => (
              <details key={k} className="faq group" >
                <summary className="flex min-h-16 cursor-pointer items-center justify-between gap-4 py-4 text-left text-[19px] font-semibold text-ink">
                  {t(`faq.${k}.q`)}
                  <Plus aria-hidden size={22} className="faq-icon shrink-0 text-neel transition-transform duration-200" />
                </summary>
                <p className="max-w-[65ch] pb-5 text-[17px] leading-relaxed text-ink-soft">{t(`faq.${k}.a`)}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* the people who built it */}
      <section id="team" aria-labelledby="team-h" className="scroll-mt-20 border-t border-rule bg-paper-raised">
        <div className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8 lg:py-24">
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:items-end">
            <h2 id="team-h" className={sectionTitle}>{t("team.title")}</h2>
            <p className="max-w-[52ch] text-lg text-ink-soft">{t("team.body")}</p>
          </div>
          <ul className="mt-12 grid gap-6 sm:grid-cols-3">
            {TEAM.map((m) => (
              <li key={m.github} className="min-w-0">
                <Image src={m.photo} alt={m.name} width={480} height={600} sizes="(min-width: 640px) 33vw, 100vw"
                  className="aspect-[4/5] w-full rounded-card border border-rule object-cover" />
                <p className="mt-4 text-xl font-semibold text-ink">{m.name}</p>
                <p className="mt-1 text-ink-soft">{t(`team.roles.${m.role}`)}</p>
                <a href={`https://github.com/${m.github}`} target="_blank" rel="noreferrer"
                  className="mt-1 inline-flex min-h-11 items-center gap-1.5 whitespace-nowrap text-[15px] font-medium text-neel underline-offset-4 hover:underline">
                  github.com/{m.github} <ExternalLink aria-hidden size={13} />
                </a>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* one closing call to action */}
      <section aria-labelledby="cta-h" className="border-t border-rule">
        <div className="mx-auto grid max-w-[1200px] gap-8 px-5 py-20 sm:px-8 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)] lg:items-center lg:py-24">
          <div className="min-w-0">
            <h2 id="cta-h" className={sectionTitle}>{t("cta.title")}</h2>
            <p className="mt-4 max-w-[56ch] text-lg text-ink-soft">{t("cta.body")}</p>
          </div>
          <div className="flex min-w-0 flex-col gap-3 sm:flex-row lg:w-full lg:max-w-[360px] lg:flex-col lg:justify-self-end">
            <Link href="/start" className={primaryBtn}>{t("cta.start")} <ArrowRight aria-hidden size={20} /></Link>
            <Link href={demo} className={secondaryBtn}>{t("cta.demo")}</Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-rule bg-paper-raised">
        <div className="mx-auto grid max-w-[1200px] grid-cols-2 gap-x-6 gap-y-10 px-5 py-14 sm:px-8 md:grid-cols-4 lg:grid-cols-[minmax(0,1.4fr)_repeat(4,minmax(0,1fr))]">
          <div className="col-span-2 max-w-[46ch] md:col-span-4 lg:col-span-1">
            <Wordmark />
            <p className="mt-4 text-[15px] text-ink-soft">{t("footer.disclaimer")}</p>
            <p className="mt-3 text-[15px] text-ink-faint">{t("footer.built")}</p>
          </div>
          <FooterCol title={t("footer.product")} links={[
            ["#how", t("footer.how")], [demo, t("footer.demo")], ["/start", t("footer.start")],
          ]} />
          <FooterCol title={t("footer.clinicians")} links={[
            ["/review", t("footer.reviewer")], ["/for-pharmacists", t("footer.pharmacists")],
          ]} />
          <FooterCol title={t("footer.trust")} links={[
            ["/privacy", t("footer.privacy")], ["/terms", t("footer.terms")], ["/contact", t("footer.contact")],
          ]} />
          <FooterCol title={t("footer.project")} links={[
            ["/docs", t("footer.docs")], [VIDEO_URL, t("footer.video")], [GITHUB_URL, t("footer.github")], ["/styleguide", t("footer.design")],
          ]} />
        </div>
      </footer>
    </div>
  );
}

function FooterCol({ title, links }: { title: string; links: [string, string][] }) {
  return (
    <nav aria-label={title} className="min-w-0">
      <p className="text-[14px] font-semibold text-ink-faint">{title}</p>
      <ul className="mt-3 grid gap-1">
        {links.map(([href, label]) => (
          <li key={href}>
            {href.startsWith("http") ? (
              <a href={href} target="_blank" rel="noreferrer" className="inline-flex min-h-10 items-center gap-1 whitespace-nowrap text-[16px] text-ink-soft hover:text-ink">
                {label} <ExternalLink aria-hidden size={13} />
              </a>
            ) : (
              <Link href={href} className="inline-flex min-h-10 items-center whitespace-nowrap text-[16px] text-ink-soft hover:text-ink">{label}</Link>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
}
