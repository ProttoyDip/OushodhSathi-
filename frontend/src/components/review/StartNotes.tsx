"use client";

import { ClipboardList } from "lucide-react";
import { useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";

/** Reviewer only: possible omissions from verified START v3 criteria, for the doctor.
 * Never a family finding: families are never told to start a medicine. Shows nothing until
 * our pharmacist has entered and verified criteria (backend/data/stopp_start.csv). */
export function StartNotes({ token, patientId }: { token: string; patientId: number }) {
  const t = useTranslations("review.start");
  const r = useApi(() => api.startNotes(token, patientId), [token, patientId]);
  if (!r.data?.length) return null;
  return (
    <section className="mt-4 rounded-card border border-dashed border-rule-strong px-4 py-3 text-sm" aria-label={t("title")}>
      <p className="flex items-center gap-2 font-semibold text-ink">
        <ClipboardList aria-hidden size={16} className="text-neel" /> {t("title")}
      </p>
      <ul className="mt-1.5 grid gap-1 text-ink">
        {r.data.map((n) => (
          <li key={n.criterion}><span className="font-semibold">{n.criterion}</span> · {n.text}</li>
        ))}
      </ul>
      <p className="mt-2 text-[13px] text-ink-faint">{t("caveat")}</p>
    </section>
  );
}
