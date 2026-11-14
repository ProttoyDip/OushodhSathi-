"use client";

import { Droplets } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { date, num } from "@/lib/format";
import { useApi } from "@/lib/useApi";

/** Reviewer only: the latest creatinine, its eGFR (CKD-EPI 2021, plain arithmetic in the backend,
 * not AI) and KDIGO stage, with a small form to enter a new result. Families see nothing from
 * this box except confirmed findings. */
export function KidneyNote({ token, patientId }: { token: string; patientId: number }) {
  const t = useTranslations("review.kidney");
  const locale = useLocale();
  const r = useApi(() => api.kidney(token, patientId), [token, patientId]);
  const [value, setValue] = useState("");
  const [unit, setUnit] = useState<"mg/dL" | "umol/L">("mg/dL");
  const [day, setDay] = useState(() => new Date().toISOString().slice(0, 10));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const d = r.data;
  if (!d) return null;
  const field = "h-9 rounded-md border border-rule-strong bg-paper px-2 text-sm text-ink";

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(undefined);
    try {
      r.setData(await api.addKidneyTest(token, patientId, { creatinine: Number(value), unit, taken_on: day, source: "lab_report" }));
      setValue("");
    } catch (err) {
      setError(err instanceof ApiError && err.status === 422 ? t("invalid") : t("error"));
    } finally {
      setBusy(false);
    }
  }

  const l = d.latest;
  return (
    <section className="mt-4 rounded-card border border-rule bg-paper-raised/60 px-4 py-3 text-sm" aria-label={t("title")}>
      <p className="flex items-center gap-2 font-semibold text-ink">
        <Droplets aria-hidden size={16} className="text-neel" />
        {t("title")}
      </p>
      {!l ? (
        <p className="mt-1.5 text-ink-soft">{t("none")}</p>
      ) : (
        <>
          <p className="tabular mt-1.5 text-ink">
            {l.egfr !== null
              ? t("egfr", { egfr: num(l.egfr, locale, 0), stage: l.stage ?? "", cr: num(l.creatinine_mg_dl, locale, 2) })
              : t("noEgfr", { cr: num(l.creatinine_mg_dl, locale, 2) })}
          </p>
          <p className="mt-0.5 text-ink-soft">
            {t("taken", { date: date(l.taken_on, locale, { day: "numeric", month: "short", year: "numeric" }) })}
          </p>
          {d.needs_sex && <p className="mt-1 text-amber">{t("needsSex")}</p>}
        </>
      )}
      <form onSubmit={save} className="mt-3 flex flex-wrap items-end gap-2">
        <label className="grid gap-1 text-[13px] text-ink-soft">
          {t("creatinine")}
          <input required type="number" inputMode="decimal" step="any" min="0" value={value}
            onChange={(e) => setValue(e.target.value)} className={`${field} tabular w-24`} />
        </label>
        <label className="grid gap-1 text-[13px] text-ink-soft">
          {t("unit")}
          <select value={unit} onChange={(e) => setUnit(e.target.value as "mg/dL" | "umol/L")} className={field}>
            <option value="mg/dL">mg/dL</option>
            <option value="umol/L">µmol/L</option>
          </select>
        </label>
        <label className="grid gap-1 text-[13px] text-ink-soft">
          {t("date")}
          <input required type="date" value={day} onChange={(e) => setDay(e.target.value)} className={field} />
        </label>
        <button type="submit" disabled={busy || !value} className="h-9 rounded-md bg-neel px-3 text-sm font-semibold text-on-neel disabled:opacity-50">
          {t("save")}
        </button>
      </form>
      {error && <p role="alert" className="mt-2 text-red">{error}</p>}
      <p className="mt-2 text-[13px] text-ink-faint">{t("caveat")}</p>
    </section>
  );
}
