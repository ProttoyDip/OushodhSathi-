"use client";

import { BookUser, Camera, ChevronRight, CircleCheck, Clock, Cpu, LineChart, ScanLine } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { SeverityBadge } from "@/components/SeverityBadge";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { date, num } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { reveal } from "@/lib/reveal";

export default function FamilyHome() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const t = useTranslations("home");
  const tc = useTranslations("common");
  const locale = useLocale();
  const patient = useApi(() => api.patient(pid), [pid]);
  const status = useApi(() => api.status(pid), [pid], 15000);
  const flags = useApi(() => api.familyFlags(pid), [pid]);

  const p = patient.data;
  const s = status.data;
  const reds = flags.data?.filter((f) => f.severity === "red").length ?? 0;

  return (
    <>
      <FamilyHeader demo={p?.is_demo} />
      <main className={`mx-auto w-full px-4 pb-12 pt-4 lg:pt-8 ${familyWidth}`}>
        {patient.error ? (
          <ErrorState error={patient.error} onRetry={patient.reload} />
        ) : !p ? (
          <Skeleton lines={3} />
        ) : (
          <div className="grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:items-start lg:gap-x-10">
            <div {...reveal(0)} className="lg:col-start-1 lg:row-start-1">
            {/* the patient, written like the head of a prescription */}
            <section aria-labelledby="patient-name" className="rounded-card border border-rule bg-paper-raised px-5 pb-4 pt-5 shadow-soft">
              <h1 id="patient-name" className="font-bn-display text-[34px] leading-[1.15] text-ink">
                {locale === "bn" ? p.name_bn ?? p.name : p.name}
              </h1>
              <p className="mt-1 text-ink-soft">
                {locale === "bn" ? p.name : p.name_bn}
                <span aria-hidden> · </span>
                <span className="tabular">{tc("years", { age: num(p.age, locale) })}</span>
                {p.district && <><span aria-hidden> · </span>{p.district}</>}
              </p>
              <div className="foil-rule my-4" />
              <p className="flex items-center gap-2 text-base text-ink-soft">
                <Clock aria-hidden size={18} />
                {p.last_checked_at ? t("lastChecked", { date: date(p.last_checked_at, locale) }) : t("neverChecked")}
              </p>
            </section>

            {/* the one primary action */}
            <div className="mt-6">
              <Link href={`/p/${pid}/scan`} className={buttonStyles.primary}>
                <Camera aria-hidden size={24} />
                {t("scanCta")}
              </Link>
              <p className="mt-2 px-1 text-base text-ink-soft">{t("scanHint")}</p>
            </div>
            </div>

            {/* confirmed results only */}
            <section {...reveal(90)} aria-labelledby="results-h" className="lg:col-start-2 lg:row-span-2 lg:row-start-1">
              <h2 id="results-h" className="font-bn-display text-[24px] leading-tight">{t("resultsTitle")}</h2>
              <div className="mt-3 rounded-card border border-rule bg-paper-raised p-5">
                {!s ? (
                  <div className="h-16 rounded-md bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />
                ) : s.review_state === "not_checked" ? (
                  <p className="text-ink-soft">{t("stateNotChecked")}</p>
                ) : s.review_state === "in_review" && s.confirmed_flags === 0 ? (
                  <>
                    <p className="flex items-start gap-3">
                      <ScanLine aria-hidden size={24} className="mt-0.5 shrink-0 text-neel" />
                      <span>{t("stateInReview")}</span>
                    </p>
                    <Link href={`/p/${pid}/status`} className={`${buttonStyles.secondary} mt-4 w-full`}>{t("seeStatus")}</Link>
                  </>
                ) : (
                  <>
                    <div className="flex flex-wrap items-center gap-2">
                      {s.confirmed_flags === 0 ? (
                        <SeverityBadge severity="green" />
                      ) : (
                        <>
                          {reds > 0 && <SeverityBadge severity="red" label={t("countRed", { count: num(reds, locale) })} />}
                          {s.confirmed_flags - reds > 0 && (
                            <SeverityBadge severity="amber" label={t("countAmber", { count: num(s.confirmed_flags - reds, locale) })} />
                          )}
                        </>
                      )}
                    </div>
                    <p className="mt-3">{t("stateReviewed", { count: s.confirmed_flags })}</p>
                    {s.review_state === "in_review" && (
                      <p className="mt-1 text-base text-ink-soft">{t("stateInReview")}</p>
                    )}
                    <Link href={`/p/${pid}/results`} className={`${buttonStyles.secondary} mt-4 w-full`}>
                      {s.confirmed_flags === 0 && <CircleCheck aria-hidden size={20} className="text-green" />}
                      {t("seeResults")}
                    </Link>
                  </>
                )}
                {s && (
                  <p className="mt-4 border-t border-rule pt-3 text-base text-ink-soft">
                    {t("medicinesOnList", { count: s.items_confirmed })}
                  </p>
                )}
              </div>
            </section>

            {/* secondary destinations */}
            <nav {...reveal(180)} aria-label={t("passport")} className="divide-y lg:col-start-1 lg:row-start-2 divide-rule overflow-hidden rounded-card border border-rule bg-paper-raised">
              <RowLink href={`/passport/${pid}`} Icon={BookUser} title={t("passport")} hint={t("passportHint")} />
              <RowLink href={`/p/${pid}/report`} Icon={LineChart} title={t("report")} hint={t("reportHint")} />
              <RowLink href="/models" Icon={Cpu} title={t("models")} hint={t("modelsHint")} />
            </nav>
          </div>
        )}
      </main>
    </>
  );
}

function RowLink({ href, Icon, title, hint }: { href: string; Icon: typeof BookUser; title: string; hint: string }) {
  return (
    <Link href={href} className="flex min-h-[72px] items-center gap-4 px-5 py-3 transition-colors hover:bg-paper-sunk/60">
      <Icon aria-hidden size={26} className="shrink-0 text-neel" />
      <span className="min-w-0 flex-1">
        <span className="block font-semibold text-ink">{title}</span>
        <span className="block text-base text-ink-soft">{hint}</span>
      </span>
      <ChevronRight aria-hidden size={22} className="shrink-0 text-ink-faint" />
    </Link>
  );
}
