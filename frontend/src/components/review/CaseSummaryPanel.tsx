"use client";

import { ChevronDown, Sparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";

/** "AI summary — check the evidence". Facts only, names checked against the record.
 * Starts collapsed after the reviewer's first 10 reviews (automation bias). Never holds a decision button. */
export function CaseSummaryPanel({ token, reviewer, patientId }: { token: string; reviewer: string; patientId: number }) {
  const t = useTranslations("review.summary");
  const s = useApi(() => api.caseSummary(token, patientId, reviewer), [token, patientId, reviewer]);
  if (!s.data) {
    return (
      <p aria-busy="true" className="mt-5 flex min-h-12 items-center gap-2 rounded-card border border-dashed border-rule-strong px-4 text-sm text-ink-soft"
        style={{ animation: "breathe 1.6s ease-in-out infinite" }}>
        <Sparkles aria-hidden size={16} className="text-neel" /> {t("title")} · {s.error ? t("none") : t("loading")}
      </p>
    );
  }
  const d = s.data;
  return (
    <details open={!d.collapsed} className="group mt-5 rounded-card border border-dashed border-rule-strong bg-paper-raised/60">
      <summary className="flex min-h-12 cursor-pointer list-none items-center gap-2 px-4 text-sm font-semibold text-ink">
        <Sparkles aria-hidden size={16} className="text-neel" />
        {t("title")}
        <span className="font-normal text-ink-faint">· {d.summary ? d.source : t("none")}</span>
        <ChevronDown aria-hidden size={16} className="ml-auto transition-transform group-open:rotate-180" />
      </summary>
      <div className="border-t border-rule px-4 py-3 text-sm">
        {d.summary ? (
          <>
            <ul className="grid list-disc gap-1 pl-5 text-ink">{d.summary.summary.map((line, i) => <li key={i}>{line}</li>)}</ul>
            {d.summary.prescribers.length > 0 && (
              <p className="mt-2 text-ink-soft">
                {d.summary.prescribers.map((p) => `${p.name}: ${p.medicines.join(", ")}`).join(" · ")}
              </p>
            )}
            {d.summary.questions_to_check.length > 0 && (
              <>
                <p className="mt-3 font-semibold text-ink">{t("questions")}</p>
                <ul className="grid list-disc gap-1 pl-5 text-ink-soft">{d.summary.questions_to_check.map((q, i) => <li key={i}>{q}</li>)}</ul>
              </>
            )}
            <p className="mt-3 text-[13px] text-ink-faint">{t("caveat")}</p>
          </>
        ) : (
          <p className="text-ink-soft">{t("dropped")}</p>
        )}
      </div>
    </details>
  );
}
