"use client";

import { Check, FlaskConical, PackageOpen, Plus } from "lucide-react";
import { useParams } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { BPTrend } from "@/components/BPTrend";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { ErrorState, Skeleton } from "@/components/States";
import { api, ApiError } from "@/lib/api";
import { cx, genericName, num } from "@/lib/format";
import type { Report } from "@/lib/types";
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
              <BPForm pid={pid} onSaved={(readings) => report.setData({ ...r, bp: { ...r.bp, readings } })} />
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

const today = () => new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD in the family's own time zone

/** Same limits as the API: top 60–260, bottom 30–160, top above bottom. */
function bpProblem(sys: number, dia: number): boolean {
  return !(sys >= 60 && sys <= 260 && dia >= 30 && dia <= 160 && sys > dia);
}

function BPForm({ pid, onSaved }: { pid: number; onSaved: (readings: Report["bp"]["readings"]) => void }) {
  const t = useTranslations("report");
  const tc = useTranslations("common");
  const [open, setOpen] = useState(false);
  const [sys, setSys] = useState("");
  const [dia, setDia] = useState("");
  const [day, setDay] = useState(today);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const field = "tabular mt-1 block h-12 w-full rounded-md border border-rule-strong bg-paper px-3 text-lg text-ink";

  if (!open) {
    return (
      <div className="mt-4 border-t border-rule pt-4">
        <button type="button" onClick={() => { setOpen(true); setMessage(null); }} className={cx(buttonStyles.secondary, "w-full sm:w-auto")}>
          <Plus aria-hidden size={20} />{t("bpAdd")}
        </button>
        {message && <p className="mt-2 flex items-center gap-1.5 text-base text-green" role="status"><Check aria-hidden size={18} />{message.text}</p>}
      </div>
    );
  }

  return (
    <form
      className="mt-4 grid gap-3 border-t border-rule pt-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const s = Number(sys), d = Number(dia);
        if (bpProblem(s, d)) {
          setMessage({ kind: "error", text: t("bpInvalid") });
          return;
        }
        setBusy(true);
        try {
          const res = await api.addBP(pid, { systolic: s, diastolic: d, taken_on: day || undefined });
          onSaved(res.readings);
          setSys("");
          setDia("");
          setOpen(false);
          setMessage({ kind: "ok", text: t("bpSaved") });
        } catch (err) {
          const status = err instanceof ApiError ? err.status : 0;
          setMessage({ kind: "error", text: status === 422 ? t("bpInvalid") : status === 429 ? tc("errorTooMany") : tc("errorGeneric") });
        } finally {
          setBusy(false);
        }
      }}
    >
      <div className="grid grid-cols-2 gap-3">
        <label className="text-base text-ink-soft">
          {t("bpTop")}
          <input required inputMode="numeric" type="number" min={60} max={260} value={sys} onChange={(e) => setSys(e.target.value)} className={field} placeholder="140" />
        </label>
        <label className="text-base text-ink-soft">
          {t("bpBottom")}
          <input required inputMode="numeric" type="number" min={30} max={160} value={dia} onChange={(e) => setDia(e.target.value)} className={field} placeholder="90" />
        </label>
      </div>
      <label className="text-base text-ink-soft">
        {t("bpDate")}
        <input type="date" value={day} max={today()} onChange={(e) => setDay(e.target.value)} className={cx(field, "sm:max-w-[220px]")} />
      </label>
      {message?.kind === "error" && <p role="alert" className="text-base text-red">{message.text}</p>}
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={busy || !sys || !dia} className={cx(buttonStyles.secondary, "flex-1 border-neel text-neel sm:flex-none")}>
          <Check aria-hidden size={20} />{busy ? t("bpSaving") : t("bpSave")}
        </button>
        <button type="button" onClick={() => { setOpen(false); setMessage(null); }} className={buttonStyles.quiet}>{tc("cancel")}</button>
      </div>
    </form>
  );
}
