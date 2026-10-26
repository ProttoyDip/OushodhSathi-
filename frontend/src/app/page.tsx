import { ArrowRight, BookOpen, ExternalLink, ShieldCheck, Stethoscope } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import { Wordmark } from "@/components/BrandMark";
import { LangToggle, ThemeToggle } from "@/components/Chrome";
import { HeroDemo } from "@/components/landing/HeroDemo";
import { FlowStrip } from "@/components/landing/FlowStrip";
import { reveal } from "@/lib/reveal";

export const metadata: Metadata = {
  title: "OushodhSathi · ওষুধসাথী — a pharmacist for every elderly home in Bangladesh",
};

const EVIDENCE = [
  { key: "e1", href: "https://www.bssnews.net/others/337437" },
  { key: "e2", href: "https://heart.bmj.com/content/heartjnl/early/2024/07/16/heartjnl-2024-324253.full.pdf" },
  { key: "e3", href: "https://www.academia.edu/111376182/Trends_of_prescribing_for_out_door_geriatric_patients_in_a_private_hospital_of_Bangladesh" },
] as const;

const SAFETY = ["r1", "r2", "r3", "r4", "r5", "r6"] as const;

export default async function Landing() {
  const t = await getTranslations("landing");
  const locale = await getLocale();
  // The accent line under each heading is always in the other language.
  const accentLang = locale === "bn" ? "en" : "bn";
  const accent = locale === "bn" ? "font-display italic" : "font-bn-display";

  return (
    <div className="min-h-dvh">
      <nav aria-label="Main" className="mx-auto flex max-w-[1200px] items-center justify-between gap-3 px-5 py-4 sm:px-8">
        <Link href="/" title={t("nav.home")} className="shrink-0"><Wordmark /></Link>
        <div className="flex items-center gap-1 sm:gap-2">
          <a href="#how" className="hidden h-11 items-center rounded-chip px-3 text-[15px] font-medium text-ink-soft hover:text-ink lg:inline-flex">{t("nav.how")}</a>
          <a href="#safe" className="hidden h-11 items-center rounded-chip px-3 text-[15px] font-medium text-ink-soft hover:text-ink lg:inline-flex">{t("nav.safe")}</a>
          <Link href="/docs" className="hidden h-11 items-center rounded-chip px-3 text-[15px] font-medium text-ink-soft hover:text-ink md:inline-flex">{t("nav.docs")}</Link>
          <Link href="/review" className="hidden h-11 items-center gap-1.5 rounded-chip border border-rule px-4 text-[15px] font-medium text-ink hover:border-rule-strong sm:inline-flex">
            <Stethoscope aria-hidden size={16} /> {t("nav.reviewer")}
          </Link>
          <ThemeToggle className="h-11 w-11" />
          <LangToggle className="h-11" />
        </div>
      </nav>

      {/* first viewport: the mechanism itself */}
      <header className="mx-auto grid max-w-[1200px] grid-cols-[minmax(0,1fr)] items-center gap-12 px-5 pb-16 pt-8 sm:px-8 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:pb-24 lg:pt-14">
        <div className="min-w-0" {...reveal(0)}>
          <h1 className="font-display text-[clamp(42px,5.6vw,76px)] leading-[1.05] text-ink">
            {t("hero.title1")} <br className="hidden sm:block" />{t("hero.title2")}
          </h1>
          <p lang={accentLang} className={`mt-4 text-[clamp(22px,2.4vw,28px)] leading-snug text-ink-soft ${accent}`}>
            {t("hero.accent")}
          </p>
          <p className="mt-6 max-w-[54ch] text-lg leading-relaxed text-ink-soft">{t("hero.body")}</p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link href="/p/1" className="press inline-flex min-h-14 items-center gap-2.5 rounded-card bg-neel px-7 text-lg font-semibold text-on-neel shadow-soft transition-colors hover:bg-neel-hover">
              {t("hero.ctaDemo")} <ArrowRight aria-hidden size={20} />
            </Link>
            <Link href="/review" className="press inline-flex min-h-14 items-center gap-2 rounded-card border border-rule-strong bg-paper-raised px-6 text-lg font-semibold text-ink hover:border-ink-faint">
              {t("hero.ctaReviewer")}
            </Link>
          </div>
          <p className="mt-4 text-[15px] text-ink-faint">{t("hero.demoNote")}</p>
        </div>
        <div className="dyed-cloth px-5 pb-6 pt-8 sm:px-8 sm:pb-8 sm:pt-10" {...reveal(140)}>
          <HeroDemo replayLabel={t("hero.replay")} />
        </div>
      </header>

      {/* how it works */}
      <section id="how" aria-labelledby="how-h" className="border-y border-rule bg-paper-raised">
        <div className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8">
          <h2 {...reveal(0)} id="how-h" className="font-display text-[clamp(36px,4.4vw,56px)] leading-none">{t("how.title")}</h2>
          <p {...reveal(60)} lang={accentLang} className={`mt-2 text-[22px] text-ink-soft ${accent}`}>{t("how.accent")}</p>
          <span aria-hidden className="stitch-x mt-6 block w-24" />
          <p {...reveal(120)} className="mt-5 max-w-[62ch] text-lg text-ink-soft">{t("how.body")}</p>
          <FlowStrip />
        </div>
      </section>

      {/* why it's safe */}
      <section id="safe" aria-labelledby="safe-h" className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8">
        <div className="grid grid-cols-[minmax(0,1fr)] gap-12 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <div {...reveal(0)}>
            <h2 id="safe-h" className="font-display text-[clamp(36px,4.4vw,56px)] leading-[1.05]">{t("safe.title")}</h2>
            <p lang={accentLang} className={`mt-3 text-[22px] text-ink-soft ${accent}`}>{t("safe.accent")}</p>
            <span aria-hidden className="stitch-x mt-6 block w-24" />
            <p className="mt-6 max-w-[48ch] text-lg text-ink-soft">{t("safe.body")}</p>
          </div>
          <ol className="grid gap-0 border-t border-rule">
            {SAFETY.map((k, i) => (
              <li key={k} {...reveal(i * 60)} className="grid grid-cols-[28px_1fr] gap-4 border-b border-rule py-5">
                <ShieldCheck aria-hidden size={22} className="mt-0.5 text-neel" />
                <div>
                  <p className="text-lg font-semibold text-ink">{t(`safe.${k}.title`)}</p>
                  <p className="mt-1 text-ink-soft">{t(`safe.${k}.body`)}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* evidence */}
      <section aria-labelledby="ev-h" className="bg-ink text-paper">
        <div className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8">
          <h2 {...reveal(0)} id="ev-h" className="max-w-[24ch] font-display text-[clamp(32px,3.8vw,48px)] leading-[1.1]">{t("evidence.title")}</h2>
          <div className="mt-12 grid gap-10 md:grid-cols-3">
            {EVIDENCE.map((e, i) => (
              <figure key={e.key} {...reveal(i * 100)} className="border-t border-paper/25 pt-5">
                <p className="tabular font-display text-[clamp(40px,4.2vw,56px)] leading-none">{t(`evidence.${e.key}.figure`)}</p>
                <p className="mt-3 text-lg leading-snug opacity-90">{t(`evidence.${e.key}.claim`)}</p>
                <figcaption className="mt-3 text-[15px] opacity-75">
                  <a href={e.href} target="_blank" rel="noreferrer" className="inline-flex items-start gap-1 underline">
                    {t(`evidence.${e.key}.source`)} <ExternalLink aria-hidden size={13} className="mt-1 shrink-0" />
                  </a>
                </figcaption>
              </figure>
            ))}
          </div>
          <p {...reveal(200)} className="mt-12 max-w-[70ch] text-[15px] opacity-75">{t("evidence.pilot")}</p>
        </div>
      </section>

      {/* team */}
      <section aria-labelledby="team-h" className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8">
        <h2 {...reveal(0)} id="team-h" className="font-display text-[clamp(32px,3.8vw,48px)] leading-none">{t("team.title")}</h2>
        <p className="mt-3 text-ink-soft">{t("team.body")}</p>
        <ul className="mt-8 grid gap-4 sm:grid-cols-3">
          {[1, 2, 3].map((n) => (
            <li key={n} {...reveal(n * 80)} className="rounded-card border border-dashed border-rule-strong p-5">
              <p className="font-semibold text-ink-soft">{t("team.member", { n })}</p>
              <p className="text-[15px] text-ink-faint">{t("team.role")}</p>
            </li>
          ))}
        </ul>
      </section>

      <footer className="border-t border-rule">
        <div className="mx-auto flex max-w-[1200px] flex-wrap items-start justify-between gap-6 px-5 py-10 sm:px-8">
          <div className="max-w-[60ch]">
            <Wordmark />
            <p className="mt-3 text-[15px] text-ink-soft">{t("footer.disclaimer")}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/docs" className="inline-flex h-11 items-center gap-1.5 rounded-chip border border-rule px-4 text-[15px] font-medium"><BookOpen aria-hidden size={16} /> {t("footer.docs")}</Link>
            <Link href="/styleguide" className="inline-flex h-11 items-center rounded-chip border border-rule px-4 text-[15px] font-medium">{t("footer.design")}</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
