"use client";

import { Activity } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { num } from "@/lib/format";
import { useApi } from "@/lib/useApi";

/** Reviewer only: a straight-line trend of home blood pressure with its 95% interval.
 * Plain arithmetic from the backend (app/stats.py), not AI, so it sits apart from the AI summary. */
export function BPTrendNote({ token, patientId }: { token: string; patientId: number }) {
  const t = useTranslations("review.bp");
  const locale = useLocale();
  const r = useApi(() => api.bpTrend(token, patientId), [token, patientId]);
  const d = r.data;
  if (!d) return null;
  const n = (v: number, digits = 0) => num(v, locale, digits);
  let line: string;
  if (d.status === "no_readings") line = t("none");
  else if (d.status === "too_few" || !d.slope) line = t("few", { n: n(d.n) });
  else {
    const s = d.slope.systolic;
    const key = d.status === "falling" ? "falling" : d.status === "rising" ? "rising" : "flat";
    const shown = key === "flat" ? s.per_week : Math.abs(s.per_week);
    line = t(key, { v: n(shown, 1), lo: n(s.ci_low, 1), hi: n(s.ci_high, 1) });
  }
  return (
    <section className="mt-4 rounded-card border border-rule bg-paper-raised/60 px-4 py-3 text-sm" aria-label={t("title")}>
      <p className="flex items-center gap-2 font-semibold text-ink">
        <Activity aria-hidden size={16} className="text-neel" />
        {t("title")}
      </p>
      <p className="tabular mt-1.5 text-ink">{line}</p>
      {d.n > 0 && d.mean && (
        <p className="tabular mt-1 text-ink-soft">
          {t("above", {
            k: n(d.above_target), n: n(d.n), s: n(d.target.systolic), d: n(d.target.diastolic),
            ms: n(d.mean.systolic), md: n(d.mean.diastolic),
          })}
        </p>
      )}
      {d.slope && <p className="mt-2 text-[13px] text-ink-faint">{t("caveat")}</p>}
    </section>
  );
}
