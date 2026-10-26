"use client";

import { FlaskConical, PackageOpen } from "lucide-react";
import { useParams } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { BPTrend } from "@/components/BPTrend";
import { FamilyHeader, familyWidth } from "@/components/Chrome";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { genericName, num } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { reveal } from "@/lib/reveal";

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const t = useTranslations("report");
  const locale = useLocale();
  const report = useApi(() => api.report(pid), [pid]);
  const r = report.data;

  return (
    <>
      <FamilyHeader back={`/p/${pid}`} demo={!!r?.demo_label} />
      <main className={`mx-auto w-full px-4 pb-12 pt-4 lg:pt-8 ${familyWidth}`}>
        <h1 className="font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t("title")}</h1>

        {report.error ? (
          <div className="mt-6"><ErrorState error={report.error} onRetry={report.reload} /></div>
        ) : !r ? (
          <Skeleton lines={4} className="mt-6" />
        ) : (
          <div className="mt-6 grid grid-cols-[minmax(0,1fr)] gap-5 lg:grid-cols-[minmax(0,1.45fr)_minmax(0,1fr)] lg:items-start">
            <section {...reveal(0)} aria-labelledby="bp-h" className="rounded-card border border-rule bg-paper-raised p-5 lg:p-7">
              <h2 id="bp-h" className="font-semibold">{t("bpTitle")}</h2>
              <div className="mt-3">
                {r.bp.readings.length ? <BPTrend readings={r.bp.readings} target={r.bp.target} /> : <p className="text-ink-soft">{t("bpNone")}</p>}
              </div>
            </section>

            <section {...reveal(90)} aria-labelledby="refill-h" className="rounded-card border border-rule bg-paper-raised p-5">
              <h2 id="refill-h" className="font-semibold">{t("refillsTitle")}</h2>
              {r.refills_due.length === 0 ? (
                <p className="mt-2 text-ink-soft">{t("refillsNone")}</p>
              ) : (
                <ul className="mt-3 divide-y divide-rule">
                  {r.refills_due.map((x) => (
                    <li key={x.brand} className="flex items-center gap-3 py-3">
                      <PackageOpen aria-hidden size={22} className="shrink-0 text-amber" />
                      <span className="min-w-0 flex-1">
                        <span className="block font-semibold">{x.brand}</span>
                        <span className="block text-base text-ink-soft">{genericName(x.generic, locale)}</span>
                      </span>
                      <span className="tabular shrink-0 text-base font-medium text-amber">
                        {t("refillDays", { days: num(x.days_left, locale) })}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section {...reveal(140)} aria-labelledby="flags-h" className="rounded-card border border-rule bg-paper-raised p-5">
              <h2 id="flags-h" className="font-semibold">{t("flagsTitle")}</h2>
              <dl className="mt-3 divide-y divide-rule">
                {[
                  [t("flagsOpen"), r.flags.confirmed_open],
                  [t("flagsResolved"), r.flags.resolved],
                  [t("flagsReviewed"), r.flags.reviewed],
                ].map(([label, value]) => (
                  <div key={label as string} className="flex items-baseline justify-between py-2.5">
                    <dt className="text-ink-soft">{label}</dt>
                    <dd className="tabular font-display text-[28px] leading-none">{num(value as number, locale)}</dd>
                  </div>
                ))}
              </dl>
            </section>

            <section {...reveal(200)} aria-labelledby="doses-h" className="rounded-card border border-dashed border-rule-strong p-5">
              <h2 id="doses-h" className="font-semibold">{t("dosesTitle")}</h2>
              {r.doses ? (
                <>
                  <p className="tabular mt-2 font-display text-[28px] leading-none">
                    {t("dosesValue", { taken: num(r.doses.taken, locale), scheduled: num(r.doses.scheduled, locale) })}
                  </p>
                  <p className="mt-3 flex items-center gap-1.5 text-base text-ink-soft">
                    <FlaskConical aria-hidden size={16} />
                    {t("dosesDemo")}
                  </p>
                </>
              ) : (
                <p className="mt-2 text-ink-soft">{t("dosesNone")}</p>
              )}
            </section>
          </div>
        )}
      </main>
    </>
  );
}
