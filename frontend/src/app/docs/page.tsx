import { ExternalLink } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import type { ReactNode } from "react";
import { Wordmark } from "@/components/BrandMark";
import { LangToggle, ThemeToggle } from "@/components/Chrome";
import { EvalPanel, LiveStatus, PilotPanel, ReviewTimePanel, SathiEvalPanel } from "@/components/docs/LivePanels";
import { reveal } from "@/lib/reveal";

export const metadata: Metadata = { title: "Docs — pitch, whitepaper, system status" };

const TOC = ["problem", "solution", "architecture", "ai", "safety", "evaluation", "status", "roadmap", "team"] as const;
const AI_ROWS = ["r1", "r2", "r3", "r4"] as const;
const AI_COLS = ["task", "model", "why", "guard"] as const;
const SAFETY = ["s1", "s2", "s3", "s4", "s5", "s6"] as const;
const ROADMAP = ["r1", "r2", "r3", "r4", "r5"] as const;

const link = (href: string) => function Linked(chunks: ReactNode) {
  return <a className="underline" href={href}>{chunks}</a>;
};
// Rich-text tags used inside the docs strings: links and code stay out of the translations.
const RICH = {
  b: (chunks: ReactNode) => <strong>{chunks}</strong>,
  code: (chunks: ReactNode) => <code className="font-mono text-[15px]">{chunks}</code>,
  bss: link("https://www.bssnews.net/others/337437"),
  ds: link("https://www.thedailystar.net/health/disease/news/hypertension-most-common-illness-country-4047686"),
  heart: link("https://heart.bmj.com/content/heartjnl/early/2024/07/16/heartjnl-2024-324253.full.pdf"),
  trend: link("https://www.academia.edu/111376182/Trends_of_prescribing_for_out_door_geriatric_patients_in_a_private_hospital_of_Bangladesh"),
};

type DocsT = Awaited<ReturnType<typeof getTranslations<"docs">>>;

export default async function Docs() {
  const t = await getTranslations("docs");
  const locale = await getLocale();
  const accentLang = locale === "bn" ? "en" : "bn";

  return (
    <div className="min-h-dvh">
      <nav className="mx-auto flex max-w-[1200px] items-center justify-between gap-3 px-5 py-4 sm:px-8">
        <Link href="/" title={t("nav.home")} className="shrink-0"><Wordmark /></Link>
        <div className="flex items-center gap-2">
          <Link href="/p/1" className="hidden h-11 items-center rounded-chip border border-rule px-4 text-[15px] font-medium sm:inline-flex">{t("nav.openDemo")}</Link>
          <ThemeToggle className="h-11 w-11" />
          <LangToggle className="h-11" />
        </div>
      </nav>

      <div className="mx-auto grid max-w-[1200px] grid-cols-[minmax(0,1fr)] gap-10 px-5 pb-24 pt-6 sm:px-8 lg:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="hidden lg:block">
          <nav aria-label={t("nav.onThisPage")} className="sticky top-6">
            <ol className="grid gap-0.5 border-l border-rule text-[15px]">
              {TOC.map((id) => (
                <li key={id}><a href={`#${id}`} className="block py-1.5 pl-4 text-ink-soft hover:text-ink">{t(`toc.${id}`)}</a></li>
              ))}
            </ol>
          </nav>
        </aside>

        <article className="min-w-0 max-w-[72ch] text-[17px] leading-relaxed text-ink [&_h2]:mt-16 [&_h2]:scroll-mt-6 [&_h2]:font-display [&_h2]:text-[40px] [&_h2]:leading-[1.1] [&_h3]:mt-8 [&_h3]:text-lg [&_h3]:font-semibold [&_p]:mt-4">
          <h1 className="font-display text-[clamp(44px,6vw,72px)] leading-[1.05]">{t("title")}</h1>
          <p lang={accentLang} className={`!mt-3 text-[24px] text-ink-soft ${accentLang === "bn" ? "font-bn-display" : "font-display italic"}`}>{t("accent")}</p>
          <p className="text-lg text-ink-soft">{t("intro")}</p>

          <h2 id="problem">{t("toc.problem")}</h2>
          <p>{t.rich("problem.body", RICH)}</p>
          <ul {...reveal(0)} className="mt-4 grid gap-3 pl-5 [list-style:disc]">
            <li>{t.rich("problem.l1", RICH)}</li>
            <li>{t.rich("problem.l2", RICH)}</li>
            <li>{t.rich("problem.l3", RICH)}</li>
          </ul>

          <h2 id="solution">{t("toc.solution")}</h2>
          <p>{t("solution.body")}</p>

          <h2 id="architecture">{t("toc.architecture")}</h2>
          <ArchitectureDiagram t={t} />

          <h2 id="ai">{t("toc.ai")}</h2>
          <p>{t.rich("ai.body", RICH)}</p>
          <div {...reveal(0)} className="mt-6 overflow-x-auto" tabIndex={0} role="region" aria-label={t("toc.ai")}>
            <table className="w-full min-w-[720px] border-collapse text-left text-[15px] leading-snug">
              <thead>
                <tr className="border-b-2 border-ink">
                  {(["hTask", "hModel", "hWhy", "hGuard"] as const).map((h) => <th key={h} className="py-2 pr-4 font-semibold">{t(`ai.${h}`)}</th>)}
                </tr>
              </thead>
              <tbody>
                {AI_ROWS.map((r) => (
                  <tr key={r} className="border-b border-rule align-top">
                    {AI_COLS.map((c, i) => (
                      <td key={c} className={i === 0 ? "py-3 pr-4 font-semibold" : "py-3 pr-4 text-ink-soft"}>{t(`ai.${r}.${c}`)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>{t.rich("ai.prompts", RICH)}</p>

          <h2 id="safety">{t("toc.safety")}</h2>
          <ol {...reveal(0)} className="mt-4 grid gap-3 pl-5 [list-style:decimal]">
            {SAFETY.map((k) => <li key={k}>{t(`safety.${k}`)}</li>)}
          </ol>
          <p>{t("safety.pdpo")}</p>
          <p>{t("safety.fhir")}</p>

          <h2 id="evaluation">{t("toc.evaluation")}</h2>
          <p>{t("evaluation.intro")}</p>
          <div {...reveal(0)} className="mt-5"><EvalPanel /></div>
          <h3>{t("evaluation.sathiTitle")}</h3>
          <p>{t("evaluation.sathiIntro")}</p>
          <div {...reveal(0)} className="mt-5"><SathiEvalPanel /></div>
          <h3>{t("evaluation.reviewTitle")}</h3>
          <p>{t("evaluation.reviewIntro")}</p>
          <div {...reveal(0)} className="mt-5"><ReviewTimePanel /></div>
          <p>{t("evaluation.tests")}</p>
          <h3>{t("evaluation.pilotTitle")}</h3>
          <p>{t("evaluation.pilotIntro")}</p>
          <div {...reveal(0)} className="mt-5"><PilotPanel /></div>

          <h2 id="status">{t("toc.status")}</h2>
          <div {...reveal(0)} className="mt-5"><LiveStatus /></div>

          <h2 id="roadmap">{t("toc.roadmap")}</h2>
          <ol {...reveal(0)} className="mt-4 grid gap-3 pl-5 [list-style:decimal]">
            {ROADMAP.map((k) => <li key={k}>{t(`roadmap.${k}`)}</li>)}
          </ol>

          <h2 id="team">{t("toc.team")}</h2>
          <p className="text-ink-soft">{t("team.placeholder")}</p>
          <p className="!mt-10 border-t border-rule pt-6 text-[15px] text-ink-soft">
            {t("footer.disclaimer")}{" "}
            <Link href="/" className="inline-flex items-center gap-1 underline">{t("footer.back")} <ExternalLink aria-hidden size={13} /></Link>
          </p>
        </article>
      </div>
    </div>
  );
}

function Box({ title, sub, tone = "plain" }: { title: string; sub?: string; tone?: "plain" | "ink" | "neel" | "foil" }) {
  const cls = {
    plain: "border-rule-strong bg-paper-raised text-ink",
    ink: "border-ink bg-ink text-paper",
    neel: "border-neel bg-neel text-on-neel",
    foil: "foil border-foil-lo text-ink",
  }[tone];
  return (
    <div className={`rounded-card border px-3 py-2.5 text-center ${cls}`}>
      <p className="text-[15px] font-semibold leading-tight">{title}</p>
      {sub && <p className="mt-0.5 text-[13px] leading-snug opacity-80">{sub}</p>}
    </div>
  );
}

function Down({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-1.5 text-[13px] text-ink-faint" aria-hidden>
      <svg width="12" height="22" viewBox="0 0 12 22"><path d="M6 0v19M1 14l5 6 5-6" fill="none" stroke="var(--rule-strong)" strokeWidth="1.5" /></svg>
      {label}
    </div>
  );
}

function ArchitectureDiagram({ t }: { t: DocsT }) {
  return (
    <figure {...reveal(0)} className="mt-6 rounded-card border border-rule bg-paper-sunk/50 p-5">
      <div className="mx-auto grid max-w-[620px]">
        <Box title={t("arch.frontend.t")} sub={t("arch.frontend.s")} />
        <Down label={t("arch.https")} />
        <Box title={t("arch.api.t")} sub={t("arch.api.s")} />
        <Down />
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="grid content-start">
            <Box tone="foil" title={t("arch.agent.t")} sub={t("arch.agent.s")} />
            <Down />
            <Box tone="foil" title={t("arch.router.t")} sub={t("arch.router.s")} />
            <Down />
            <Box title={t("arch.providers.t")} sub={t("arch.providers.s")} />
          </div>
          <div className="grid content-start">
            <Box title={t("arch.matcher.t")} sub={t("arch.matcher.s")} />
            <Down label={t("arch.confirmedItems")} />
            <Box tone="ink" title={t("arch.rules.t")} sub={t("arch.rules.s")} />
          </div>
          <div className="grid content-start">
            <Box title={t("arch.sqlite.t")} sub={t("arch.sqlite.s")} />
            <Down label={t("arch.pendingFlags")} />
            <Box tone="neel" title={t("arch.gate.t")} sub={t("arch.gate.s")} />
            <Down label={t("arch.confirmedOnly")} />
            <Box title={t("arch.family.t")} sub={t("arch.family.s")} />
          </div>
        </div>
      </div>
      <figcaption className="mt-4 text-[13px] text-ink-faint">{t("arch.caption")}</figcaption>
    </figure>
  );
}
