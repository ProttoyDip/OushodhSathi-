import {
  ArrowRight, BookOpen, CircleCheck, Clock, ExternalLink, ImageOff, Languages, Plus, ShieldCheck, Stethoscope,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import { Wordmark } from "@/components/BrandMark";
import { LangToggle, ThemeToggle } from "@/components/Chrome";
import { WarmUp } from "@/components/JudgeBar";
import { HowTimeline } from "@/components/landing/HowTimeline";
import { ProductFrames } from "@/components/landing/ProductFrames";
import { stickyBar } from "@/lib/layout";
import { reveal } from "@/lib/reveal";
import { demoHref, GITHUB_URL } from "@/lib/site";
import { Analytics } from "@vercel/analytics/next";

export const metadata: Metadata = {
  title: "OushodhSathi · ওষুধসাথী — a pharmacist for every elderly home in Bangladesh",
};

const EVIDENCE = [
  { key: "e1", href: "https://www.bssnews.net/others/337437" },
  { key: "e2", href: "https://heart.bmj.com/content/heartjnl/early/2024/07/16/heartjnl-2024-324253.full.pdf" },
  { key: "e3", href: "https://www.academia.edu/111376182/Trends_of_prescribing_for_out_door_geriatric_patients_in_a_private_hospital_of_Bangladesh" },
] as const;

const FAQ = ["q1", "q2", "q3", "q4", "q5", "q6"] as const;

const sectionTitle = "font-display text-[clamp(34px,4.2vw,54px)] leading-[1.05] text-ink";
const navLink = "hidden h-11 items-center rounded-chip px-3 text-[15px] font-medium text-ink-soft hover:text-ink";
const primaryBtn = "press inline-flex min-h-14 items-center justify-center gap-2.5 rounded-card bg-neel px-7 text-lg font-semibold text-on-neel shadow-soft transition-colors hover:bg-neel-hover";
const secondaryBtn = "press inline-flex min-h-14 items-center justify-center gap-2 rounded-card border border-rule-strong bg-paper-raised px-6 text-lg font-semibold text-ink hover:border-ink-faint";

export default async function Landing() {
  const t = await getTranslations("landing");
  const locale = await getLocale();
  // The accent line under each heading is always in the other language.
  const accentLang = locale === "bn" ? "en" : "bn";
  const accent = locale === "bn" ? "font-display italic" : "font-bn-display";
  const demo = demoHref("/p/1");

  return (
    <div className="min-h-dvh">
      <WarmUp />
      <Analytics />
      <div className={stickyBar}>
        <nav aria-label="Main" className="mx-auto flex max-w-[1200px] items-center justify-between gap-3 px-5 py-3 sm:px-8">
          <Link href="/" title={t("nav.home")} className="shrink-0"><Wordmark /></Link>
          <div className="flex items-center gap-1 sm:gap-2">
            <a href="#how" className={`${navLink} lg:inline-flex`}>{t("nav.how")}</a>
            <a href="#safe" className={`${navLink} lg:inline-flex`}>{t("nav.safe")}</a>
            <a href="#faq" className={`${navLink} lg:inline-flex`}>{t("nav.faq")}</a>
            <Link href="/docs" className={`${navLink} md:inline-flex`}>{t("nav.docs")}</Link>
            <Link href="/review" className="hidden h-11 items-center gap-1.5 rounded-chip border border-rule px-4 text-[15px] font-medium text-ink hover:border-rule-strong sm:inline-flex">
              <Stethoscope aria-hidden size={16} /> {t("nav.reviewer")}
            </Link>
            <ThemeToggle className="h-11 w-11" />
            <LangToggle className="h-11" />
          </div>
        </nav>
      </div>

      {/* hero: the claim, then both sides of the product */}
      <header className="mx-auto max-w-[1200px] px-5 pb-16 pt-10 sm:px-8 lg:pb-24 lg:pt-16">
        <div className="mx-auto max-w-[880px] text-center" {...reveal(0)}>
          <p className="inline-flex items-center gap-3 text-[15px] font-semibold text-neel">
            <span aria-hidden className="stitch-x w-8" /> {t("hero.eyebrow")} <span aria-hidden className="stitch-x w-8" />
          </p>
          <h1 className="mt-5 font-display text-[clamp(40px,6vw,80px)] leading-[1.04] text-ink">
            {t("hero.title1")} <br className="hidden sm:block" />{t("hero.title2")}
          </h1>
          <p lang={accentLang} className={`mt-4 text-[clamp(20px,2.3vw,27px)] leading-snug text-ink-soft ${accent}`}>
            {t("hero.accent")}
          </p>
          <p className="mx-auto mt-6 max-w-[62ch] text-lg leading-relaxed text-ink-soft">{t("hero.body")}</p>
          <div className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
            <Link href={demo} className={primaryBtn}>{t("hero.ctaDemo")} <ArrowRight aria-hidden size={20} /></Link>
            <Link href="/start" className={secondaryBtn}>{t("hero.ctaStart")}</Link>
          </div>
          <p className="mt-3 text-[15px] text-ink-faint">{t("hero.demoNote")}</p>
          <ul className="mx-auto mt-8 flex max-w-[760px] flex-wrap justify-center gap-x-6 gap-y-3 text-[15px] font-medium text-ink-soft">
            {([["trust1", ShieldCheck], ["trust2", Languages], ["trust3", ImageOff]] as const).map(([k, Icon]) => (
              <li key={k} className="inline-flex items-center gap-2"><Icon aria-hidden size={18} className="shrink-0 text-neel" /> {t(`hero.${k}`)}</li>
            ))}
          </ul>
        </div>
        <div className="mt-12 lg:mt-16" {...reveal(160)}>
          <ProductFrames replayLabel={t("hero.replay")} reviewLabel={t("hero.frameReview")} phoneLabel={t("hero.framePhone")} />
        </div>
      </header>

      {/* how it works */}
      <section id="how" aria-labelledby="how-h" className="scroll-mt-20 border-y border-rule bg-paper-raised">
        <div className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8 lg:py-24">
          <h2 {...reveal(0)} id="how-h" className={sectionTitle}>{t("how.title")}</h2>
          <p {...reveal(60)} lang={accentLang} className={`mt-2 text-[22px] text-ink-soft ${accent}`}>{t("how.accent")}</p>
          <span aria-hidden className="stitch-x mt-6 block w-24" />
          <p {...reveal(120)} className="mt-5 max-w-[62ch] text-lg text-ink-soft">{t("how.body")}</p>
          <HowTimeline />
        </div>
      </section>

      {/* why it's safe: a bento of the six promises */}
      <section id="safe" aria-labelledby="safe-h" className="mx-auto max-w-[1200px] scroll-mt-20 px-5 py-20 sm:px-8 lg:py-24">
        <div {...reveal(0)} className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:items-end lg:gap-12">
          <div>
            <h2 id="safe-h" className={sectionTitle}>{t("safe.title")}</h2>
            <p lang={accentLang} className={`mt-3 text-[22px] text-ink-soft ${accent}`}>{t("safe.accent")}</p>
            <span aria-hidden className="stitch-x mt-6 block w-24" />
          </div>
          <p className="max-w-[52ch] text-lg text-ink-soft">{t("safe.body")}</p>
        </div>
        <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-3">

          {/* the promise everything else rests on */}
          <article {...reveal(60)} className="flex flex-col justify-between gap-8 rounded-card border border-neel bg-neel-tint p-6 md:col-span-2 lg:p-8">
            <div>
              <ShieldCheck aria-hidden size={28} className="text-neel" />
              <h3 className="mt-4 max-w-[26ch] font-display text-[clamp(26px,2.6vw,34px)] leading-[1.1] text-ink">{t("safe.r2.title")}</h3>
              <p className="mt-3 max-w-[60ch] text-lg text-ink-soft">{t("safe.r2.body")}</p>
            </div>
            <div aria-hidden className="flex flex-wrap items-center gap-2 text-[15px] font-semibold">
              <span className="inline-flex items-center gap-1.5 rounded-chip border border-rule-strong bg-paper px-3 py-1.5 text-ink-soft"><Clock size={15} /> {t("flow.s4.title")}</span>
              <span className="stitch-x w-8" />
              <span className="inline-flex items-center gap-1.5 rounded-chip border border-neel bg-paper px-3 py-1.5 text-neel"><Stethoscope size={15} /> {t("flow.s5.title")}</span>
              <span className="stitch-x w-8" />
              <span className="inline-flex items-center gap-1.5 rounded-chip border border-rule-strong bg-paper px-3 py-1.5 text-ink"><CircleCheck size={15} /> {t("flow.s6.title")}</span>
            </div>
          </article>

          {(["r1", "r3", "r4", "r5", "r6"] as const).map((k, i) => (
            <article key={k} {...reveal(100 + i * 50)} className="rounded-card border border-rule bg-paper-raised p-6">
              <ShieldCheck aria-hidden size={22} className="text-neel" />
              <h3 className="mt-3 text-[20px] font-semibold leading-snug text-ink">{t(`safe.${k}.title`)}</h3>
              <p className="mt-2 text-ink-soft">{t(`safe.${k}.body`)}</p>
            </article>
          ))}
          <Link href="/docs" {...reveal(360)}
            className="group flex flex-col justify-between rounded-card border border-dashed border-rule-strong p-6 transition-colors hover:border-neel lg:col-span-2">
            <BookOpen aria-hidden size={22} className="text-neel" />
            <span className="mt-6">
              <span className="flex items-center gap-2 text-[20px] font-semibold text-ink">
                {t("safe.docsTitle")} <ArrowRight aria-hidden size={18} className="transition-transform group-hover:translate-x-0.5" />
              </span>
              <span className="mt-1 block text-ink-soft">{t("safe.docsBody")}</span>
            </span>
          </Link>
        </div>
      </section>

      {/* evidence: public numbers, each with its source */}
      <section aria-labelledby="ev-h" className="border-y border-rule bg-paper-raised">
        <div className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8">
          <h2 {...reveal(0)} id="ev-h" className={`max-w-[24ch] ${sectionTitle}`}>{t("evidence.title")}</h2>
          <div className="mt-12 grid gap-10 md:grid-cols-3">
            {EVIDENCE.map((e, i) => (
              <figure key={e.key} {...reveal(i * 100)} className="border-t-2 border-neel pt-5">
                <p className="flex flex-wrap items-baseline gap-x-3">
                  <span className="tabular font-display text-[clamp(52px,5vw,72px)] leading-none text-neel">{t(`evidence.${e.key}.figure`)}</span>
                  {t(`evidence.${e.key}.unit`) && <span className="text-lg font-semibold text-ink">{t(`evidence.${e.key}.unit`)}</span>}
                </p>
                <p className="mt-4 text-lg leading-snug text-ink">{t(`evidence.${e.key}.claim`)}</p>
                <figcaption className="mt-3 text-[15px] text-ink-faint">
                  <a href={e.href} target="_blank" rel="noreferrer" className="inline-flex items-start gap-1 underline underline-offset-4 hover:text-ink">
                    {t(`evidence.${e.key}.source`)} <ExternalLink aria-hidden size={13} className="mt-1 shrink-0" />
                  </a>
                </figcaption>
              </figure>
            ))}
          </div>
          <p {...reveal(200)} className="mt-12 max-w-[70ch] rounded-card border border-dashed border-rule-strong px-4 py-3 text-[15px] text-ink-soft">{t("evidence.pilot")}</p>
        </div>
      </section>

      {/* questions families ask */}
      <section id="faq" aria-labelledby="faq-h" className="mx-auto max-w-[1200px] scroll-mt-20 px-5 py-20 sm:px-8 lg:py-24">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
          <div {...reveal(0)}>
            <h2 id="faq-h" className={sectionTitle}>{t("faq.title")}</h2>
            <p lang={accentLang} className={`mt-3 text-[22px] text-ink-soft ${accent}`}>{t("faq.accent")}</p>
            <span aria-hidden className="stitch-x mt-6 block w-24" />
          </div>
          <div className="divide-y divide-rule border-y border-rule">
            {FAQ.map((k, i) => (
              <details key={k} className="faq group" {...reveal(i * 50)}>
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

      {/* one closing call to action */}
      <section aria-labelledby="cta-h" className="mx-auto max-w-[1200px] px-5 pb-20 sm:px-8 lg:pb-24">
        <div {...reveal(0)} className="relative overflow-hidden rounded-card border border-rule-strong bg-paper-raised px-6 py-12 text-center sm:px-12 lg:py-16">
          <span aria-hidden className="stitch-x absolute inset-x-6 top-4 sm:inset-x-12" />
          <h2 id="cta-h" className={sectionTitle}>{t("cta.title")}</h2>
          <p className="mx-auto mt-4 max-w-[58ch] text-lg text-ink-soft">{t("cta.body")}</p>
          <div className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
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
            ["/docs", t("footer.docs")], [GITHUB_URL, t("footer.github")], ["/styleguide", t("footer.design")],
          ]} />
        </div>
      </footer>
    </div>
  );
}

function FooterCol({ title, links }: { title: string; links: [string, string][] }) {
  return (
    <nav aria-label={title}>
      <p className="text-[14px] font-semibold uppercase tracking-[0.08em] text-ink-faint">{title}</p>
      <ul className="mt-3 grid gap-1">
        {links.map(([href, label]) => (
          <li key={href}>
            {href.startsWith("http") ? (
              <a href={href} target="_blank" rel="noreferrer" className="inline-flex min-h-10 items-center gap-1 text-[16px] text-ink-soft hover:text-ink">
                {label} <ExternalLink aria-hidden size={13} />
              </a>
            ) : (
              <Link href={href} className="inline-flex min-h-10 items-center text-[16px] text-ink-soft hover:text-ink">{label}</Link>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
}
