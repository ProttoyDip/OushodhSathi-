"use client";

import { ListChecks } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { num } from "@/lib/format";
import { useApi } from "@/lib/useApi";

/** Reviewer only: 14-day adherence per medicine from the family's taken / not-taken ticks,
 * with a 95% Wilson interval and how many expected doses were recorded at all, so missing
 * data is visible. Arithmetic in the backend (app/stats.py), not AI. Families never see these numbers. */
export function AdherenceNote({ token, patientId }: { token: string; patientId: number }) {
  const t = useTranslations("review.adherence");
  const locale = useLocale();
  const r = useApi(() => api.adherence(token, patientId), [token, patientId]);
  const d = r.data;
  if (!d || d.medicines.length === 0) return null;
  const pct = (v: number) => num(Math.round(v * 100), locale);
  return (
    <section className="mt-4 rounded-card border border-rule bg-paper-raised/60 px-4 py-3 text-sm" aria-label={t("title")}>
      <p className="flex items-center gap-2 font-semibold text-ink">
        <ListChecks aria-hidden size={16} className="text-neel" />
        {t("title", { days: num(d.days, locale) })}
      </p>
      {d.household.recorded === 0 ? (
        <p className="mt-1.5 text-ink-soft">{t("none")}</p>
      ) : (
        <ul className="mt-1.5 grid gap-1">
          {d.medicines.map((m) => (
            <li key={m.item_id} className="tabular text-ink">
              <span className="font-semibold">{m.brand}</span>{" "}
              {m.adherence
                ? t("line", { taken: num(m.taken, locale), recorded: num(m.recorded, locale), p: pct(m.adherence.p),
                    lo: pct(m.adherence.ci_low), hi: pct(m.adherence.ci_high) })
                : t("noTicks")}
              <span className="text-ink-soft"> · {t("coverage", { recorded: num(m.recorded, locale), expected: num(m.expected, locale) })}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-[13px] text-ink-faint">{t("caveat")}</p>
    </section>
  );
}
