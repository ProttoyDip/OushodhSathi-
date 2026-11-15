"use client";

import { PhoneCall } from "lucide-react";
import { useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";

/** Reviewer only: the household's recent check-in calls and how many were answered. */
export function CallHistoryNote({ token, patientId }: { token: string; patientId: number }) {
  const t = useTranslations("calls.review");
  const h = useApi(() => api.callHistory(token, patientId), [token, patientId]);
  const d = h.data;
  if (!d || (!d.active && d.attempts.length === 0)) return null;
  const r = d.answer_rate;
  return (
    <section className="mt-5 rounded-card border border-rule px-4 py-3 text-sm">
      <h3 className="flex items-center gap-2 font-semibold text-ink">
        <PhoneCall aria-hidden size={16} className="text-neel" /> {t("title")}
        <span className="font-normal text-ink-faint">· {d.active ? t("on", { time: d.local_time ?? "" }) : t("off")}</span>
      </h3>
      {r ? (
        <p className="mt-1 text-ink-soft">
          {t("rate", { k: r.k, n: r.n, p: Math.round(r.p * 100), lo: Math.round(r.ci_low * 100), hi: Math.round(r.ci_high * 100) })}
        </p>
      ) : (
        <p className="mt-1 text-ink-faint">{t("none")}</p>
      )}
      <ul className="mt-2 grid gap-1 text-ink-soft">
        {d.attempts.slice(0, 7).map((a, i) => (
          <li key={i}>
            {a.day} #{a.attempt_no} · {t(`status.${a.status}`)}
            {Object.keys(a.answers).length > 0 && ` · ${Object.entries(a.answers).map(([s, v]) => `${t(`slot.${s}`)} ${t(v)}`).join(", ")}`}
          </li>
        ))}
      </ul>
    </section>
  );
}
