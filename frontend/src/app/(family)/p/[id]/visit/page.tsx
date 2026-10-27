"use client";

import { Camera, Mic, Minus, Plus, Printer, X } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { BPTrend } from "@/components/BPTrend";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { SeverityBadge } from "@/components/SeverityBadge";
import { useSpeechInput } from "@/components/sathi/speech";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { cx, date, genericName } from "@/lib/format";
import { useApi } from "@/lib/useApi";

/** Before the doctor visit: one printable page with everything the doctor should see. */
export default function VisitPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const router = useRouter();
  const t = useTranslations("visit");
  const tp = useTranslations("passport");
  const locale = useLocale();
  const visit = useApi(() => api.visit(pid), [pid]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const speech = useSpeechInput(locale === "bn" ? "bn-BD" : "en-US", (text) => setQuestion((q) => (q ? `${q} ${text}` : text)));
  const v = visit.data;

  async function saveQuestions(list: string[]) {
    if (!v) return;
    visit.setData({ ...v, questions: list });
    await api.patchPatient(pid, { visit_questions: list }).catch(() => visit.reload());
  }

  async function done() {
    setBusy(true);
    try {
      router.push((await api.visitDone(pid)).next);
    } catch {
      setBusy(false);
    }
  }

  return (
    <>
      <FamilyHeader back={`/p/${pid}`} demo={!!v?.demo_label} />
      <style>{`@media print { @page { size: A4 portrait; margin: 12mm; } }`}</style>
      <main className={`mx-auto w-full px-4 pb-12 pt-4 lg:pt-8 ${familyWidth}`}>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t("title")}</h1>
            {v && (
              <p className="mt-1 text-ink-soft">
                {locale === "bn" ? v.patient.name_bn ?? v.patient.name : v.patient.name} · {v.patient.age}
                {" · "}{v.last_visit_at ? t("since", { date: date(v.last_visit_at, locale) }) : t("firstVisit")}
              </p>
            )}
          </div>
          <button type="button" onClick={() => window.print()} className={cx(buttonStyles.secondary, "no-print")}>
            <Printer aria-hidden size={20} /> {t("print")}
          </button>
        </div>

        {visit.error ? (
          <div className="mt-6"><ErrorState error={visit.error} onRetry={visit.reload} /></div>
        ) : !v ? (
          <Skeleton lines={4} className="mt-6" />
        ) : (
          <div className="mt-6 grid grid-cols-[minmax(0,1fr)] gap-5 lg:grid-cols-2 print:grid-cols-1">
            <Section title={t("medicines", { count: v.medicines.length })}>
              <ul className="divide-y divide-rule">
                {v.medicines.map((m, i) => (
                  <li key={i} className="py-2.5">
                    <p className="font-semibold">{m.generic ? genericName(m.generic, locale) : m.brand}
                      <span className="font-normal text-ink-soft"> · {m.brand}{m.strength ? ` ${m.strength}` : ""}</span></p>
                    <p className="text-[15px] text-ink-soft">
                      {m.schedule.length ? m.schedule.map((s) => tp(s)).join(" · ") : tp("asNeeded")}
                      {m.per_dose > 1 ? ` · × ${m.per_dose}` : ""}
                      {m.prescriber ? ` · ${m.prescriber}` : ""}
                    </p>
                  </li>
                ))}
              </ul>
              {v.allergies.length > 0 && <p className="mt-3 font-semibold text-red">{tp("allergies")}: {v.allergies.join(", ")}</p>}
            </Section>

            <Section title={t("changes")}>
              {v.changes.length === 0 ? (
                <p className="text-ink-soft">{v.last_visit_at ? t("noChanges") : t("changesFirst")}</p>
              ) : (
                <ul className="grid gap-2">
                  {v.changes.map((c, i) => (
                    <li key={i} className="flex items-start gap-2">
                      {c.kind === "added" ? <Plus aria-hidden size={18} className="mt-1 shrink-0 text-green" /> : <Minus aria-hidden size={18} className="mt-1 shrink-0 text-red" />}
                      <span>
                        <b className="font-semibold">{c.brand}</b> {c.kind === "added" ? t("added") : t("stopped")}
                        <span className="block text-[15px] text-ink-soft">{[c.by, c.at ? date(c.at, locale) : null].filter(Boolean).join(" · ")}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            <Section title={t("findings")}>
              {v.findings.length === 0 ? <p className="text-ink-soft">{t("noFindings")}</p> : (
                <ul className="grid gap-3">
                  {v.findings.map((f, i) => (
                    <li key={i} className="grid grid-cols-[auto_1fr] items-start gap-x-3">
                      <SeverityBadge severity={f.severity} size="sm" />
                      <span><b className="font-semibold">{f.brands.join(" + ")}</b>
                        {f.note && <span className="block text-[15px] text-ink-soft">{f.note}{f.reviewer ? ` (${f.reviewer})` : ""}</span>}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            <Section title={t("bp")}>
              {v.bp.length ? <BPTrend readings={v.bp} /> : <p className="text-ink-soft">{t("noBp")}</p>}
            </Section>

            <Section title={t("questions")} className="lg:col-span-2">
              <p className="text-[15px] text-ink-soft print:hidden">{t("questionsHint")}</p>
              <ol className="mt-2 grid list-decimal gap-1.5 pl-6">
                {v.questions.map((q, i) => (
                  <li key={i} className="pl-1">
                    <span className="flex items-start justify-between gap-2">
                      <span className="min-w-0 break-words">{q}</span>
                      <button type="button" aria-label={t("removeQuestion")} onClick={() => saveQuestions(v.questions.filter((_, j) => j !== i))}
                        className="no-print inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-ink-soft hover:text-ink">
                        <X aria-hidden size={18} />
                      </button>
                    </span>
                  </li>
                ))}
              </ol>
              <form className="no-print mt-3 flex items-end gap-2" onSubmit={(e) => {
                e.preventDefault();
                if (question.trim()) { saveQuestions([...v.questions, question.trim()]); setQuestion(""); }
              }}>
                <label className="min-w-0 flex-1 text-base text-ink-soft">{t("addQuestion")}
                  <input value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={300}
                    className="mt-1 block h-12 w-full rounded-md border border-rule-strong bg-paper px-3 text-lg text-ink" />
                </label>
                <button type="button" onClick={speech.toggle} aria-pressed={speech.listening} aria-label={t("speak")}
                  className={cx("press inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full border",
                    speech.listening ? "border-red bg-red-tint text-red" : "border-rule-strong text-ink-soft")}>
                  <Mic aria-hidden size={22} />
                </button>
                <button type="submit" disabled={!question.trim()} className={cx(buttonStyles.secondary, "shrink-0 px-4")}>
                  <Plus aria-hidden size={18} /> {t("add")}
                </button>
              </form>
              {speech.note && <p className="no-print mt-2 text-[15px] text-ink-soft">{t(`mic.${speech.note}`)}</p>}
              {v.pharmacist_questions.some((q) => q.reply) && (
                <div className="mt-4 border-t border-rule pt-3">
                  <h3 className="text-[15px] font-semibold text-ink-soft">{t("pharmacistAnswers")}</h3>
                  <ul className="mt-1 grid gap-2 text-[15px]">
                    {v.pharmacist_questions.filter((q) => q.reply).map((q, i) => (
                      <li key={i}><b className="font-semibold">{q.text}</b><span className="block text-ink-soft">{q.reply} ({q.replied_by})</span></li>
                    ))}
                  </ul>
                </div>
              )}
            </Section>

            <div className="no-print rounded-card border border-neel/40 bg-neel-tint/40 p-5 lg:col-span-2">
              <p className="font-semibold">{t("afterTitle")}</p>
              <p className="mt-1 text-base text-ink-soft">{t("afterBody")}</p>
              <button type="button" disabled={busy} onClick={done} className={cx(buttonStyles.primary, "mt-4 lg:w-auto lg:min-w-[360px]")}>
                <Camera aria-hidden size={22} /> {t("afterCta")}
              </button>
            </div>
            <p className="text-[13px] text-ink-faint lg:col-span-2">{t("generated", { date: date(v.generated_at, locale) })}{v.demo_label ? ` · ${v.demo_label}` : ""}</p>
          </div>
        )}
      </main>
    </>
  );
}

function Section({ title, children, className }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <section className={cx("break-inside-avoid rounded-card border border-rule bg-paper-raised p-5 print:border-ink", className)}>
      <h2 className="mb-3 font-semibold">{title}</h2>
      {children}
    </section>
  );
}
