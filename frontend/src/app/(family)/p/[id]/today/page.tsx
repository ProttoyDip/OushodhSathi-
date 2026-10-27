"use client";

import { Clock, Moon, MoonStar, NotebookPen, Pill, Printer, Sun, Sunrise, Sunset, Volume2 } from "lucide-react";
import { useParams } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { RamadanSafetyCard } from "@/components/RamadanSafetyCard";
import { useVoice } from "@/components/sathi/speech";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { cx, date, genericName } from "@/lib/format";
import { reveal } from "@/lib/reveal";
import { loadThumbs } from "@/lib/thumbs";
import type { Slot, TodayMedicine } from "@/lib/types";
import { useApi } from "@/lib/useApi";

const SLOTS: { key: Slot; Icon: typeof Sun; tone: string }[] = [
  { key: "morning", Icon: Sunrise, tone: "text-amber" },
  { key: "noon", Icon: Sun, tone: "text-amber" },
  { key: "night", Icon: Moon, tone: "text-neel" },
];
// an approved Ramadan plan: before dawn and at sunset
const FAST_SLOTS: { key: "sehri" | "iftar"; Icon: typeof Sun; tone: string }[] = [
  { key: "sehri", Icon: MoonStar, tone: "text-neel" },
  { key: "iftar", Icon: Sunset, tone: "text-amber" },
];
const BN_COUNT = ["", "একটি", "দুটি", "তিনটি", "চারটি", "পাঁচটি", "ছয়টি", "সাতটি", "আটটি", "নয়টি", "দশটি"];
const EN_COUNT = ["", "one tablet", "two tablets", "three tablets", "four tablets", "five tablets", "six tablets",
  "seven tablets", "eight tablets", "nine tablets", "ten tablets"];

/** Today's medicines, made to work without reading: time as pictures, the strip's own photo,
 * tablets drawn as shapes, and "Listen". Only the times a pharmacist approved appear here. */
export default function TodayPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const t = useTranslations("today");
  const tp = useTranslations("passport");
  const locale = useLocale();
  const today = useApi(() => api.today(pid), [pid]);
  const [thumbs, setThumbs] = useState<Record<number, string>>({});
  useEffect(() => setThumbs(loadThumbs(pid)), [pid]);
  const d = today.data;

  const ramadan = d?.ramadan ?? null;
  const say = (label: string, list: TodayMedicine[]) => `${label}: ${list.map((m) => (locale === "bn"
    ? `${m.brand} ${BN_COUNT[m.per_dose] ?? m.per_dose}`
    : `${m.brand}, ${EN_COUNT[m.per_dose] ?? `${m.per_dose} tablets`}`)).join(locale === "bn" ? ", " : "; ")}।`;
  const spoken = !d ? "" : ramadan
    ? FAST_SLOTS.filter(({ key }) => ramadan[key].length).map(({ key }) => say(t(key), ramadan[key])).join(" ")
    : SLOTS.filter(({ key }) => d.slots[key].length).map(({ key }) => say(tp(key), d.slots[key])).join(" ");

  return (
    <>
      <FamilyHeader back={`/p/${pid}`} demo={!!d?.demo_label} />
      <style>{`@media print { @page { size: A4 portrait; margin: 12mm; } }`}</style>
      <main className={`mx-auto w-full px-4 pb-12 pt-4 lg:pt-8 ${familyWidth}`}>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="font-bn-display text-[34px] leading-[1.2] lg:text-[44px] print:text-[40px]">{t("title")}</h1>
            <p className="mt-1 text-ink-soft print:hidden">{t("intro")}</p>
          </div>
          <div className="no-print flex flex-wrap gap-2">
            {spoken && <ListenSchedule text={spoken} />}
            <button type="button" onClick={() => window.print()} className={buttonStyles.secondary}>
              <Printer aria-hidden size={20} /> {t("print")}
            </button>
          </div>
        </div>

        {today.error ? (
          <div className="mt-6"><ErrorState error={today.error} onRetry={today.reload} /></div>
        ) : !d ? (
          <Skeleton lines={3} className="mt-6" />
        ) : (
          <>
            {d.waiting_approval > 0 && (
              <p className="no-print mt-5 flex items-start gap-2 rounded-card border border-dashed border-rule-strong p-4 text-base text-ink-soft">
                <Clock aria-hidden size={20} className="mt-0.5 shrink-0" /> {t("waiting", { count: d.waiting_approval })}
              </p>
            )}
            {ramadan ? (
              <>
                <p className="mt-5 inline-flex items-center gap-2 rounded-chip bg-neel-tint px-4 py-1.5 font-semibold text-neel">
                  <MoonStar aria-hidden size={18} /> {t("ramadanOn")}
                </p>
                <div className="mt-4 grid gap-5 lg:grid-cols-2 print:grid-cols-1">
                  {FAST_SLOTS.map(({ key, Icon, tone }, i) => (
                    <section key={key} {...reveal(i * 90)} aria-labelledby={`slot-${key}`}
                      className="break-inside-avoid rounded-card border border-rule bg-paper-raised p-5 print:border-2 print:border-ink">
                      <h2 id={`slot-${key}`} className="flex items-center gap-3">
                        <Icon aria-hidden size={52} strokeWidth={1.75} className={cx("shrink-0 print:text-ink", tone)} />
                        <span className="font-bn-display text-[30px] leading-none">{t(key)}</span>
                      </h2>
                      {ramadan[key].length === 0 ? <p className="mt-4 text-ink-faint">{t("nothing")}</p> : (
                        <ul className="mt-4 grid gap-3">
                          {ramadan[key].map((m) => <Row key={m.id} m={m} thumb={thumbs[m.id]} locale={locale} />)}
                        </ul>
                      )}
                    </section>
                  ))}
                </div>
                {ramadan.note && (
                  <p className="mt-5 flex items-start gap-2 rounded-card border border-rule bg-paper-raised p-4">
                    <NotebookPen aria-hidden size={20} className="mt-1 shrink-0 text-neel" />
                    <span><b className="font-semibold">{t("clinicianNote", { name: ramadan.approved_by ?? "" })}</b> {ramadan.note}
                      {ramadan.approved_at && <span className="block text-[15px] text-ink-faint">{date(ramadan.approved_at, locale)}</span>}</span>
                  </p>
                )}
                {ramadan.not_in_plan.length > 0 && (
                  <section aria-labelledby="not-in-plan" className="mt-5 rounded-card border border-dashed border-amber-line p-5">
                    <h2 id="not-in-plan" className="font-semibold text-amber">{t("notInPlan")}</h2>
                    <ul className="mt-3 grid gap-3">
                      {ramadan.not_in_plan.map((m) => <Row key={m.id} m={m} thumb={thumbs[m.id]} locale={locale} />)}
                    </ul>
                  </section>
                )}
                <div className="mt-5"><RamadanSafetyCard /></div>
                <button type="button" onClick={async () => { await api.ramadanEnd(pid); today.reload(); }}
                  className={cx(buttonStyles.quiet, "no-print mt-3 px-2")}>{t("ramadanEnd")}</button>
              </>
            ) : (
            <div className="mt-6 grid gap-5 lg:grid-cols-3 print:grid-cols-1 print:gap-3">
              {SLOTS.map(({ key, Icon, tone }, i) => (
                <section key={key} {...reveal(i * 90)} aria-labelledby={`slot-${key}`}
                  className="break-inside-avoid rounded-card border border-rule bg-paper-raised p-5 print:border-2 print:border-ink">
                  <h2 id={`slot-${key}`} className="flex items-center gap-3">
                    <Icon aria-hidden size={52} strokeWidth={1.75} className={cx("shrink-0 print:text-ink", tone)} />
                    <span className="font-bn-display text-[30px] leading-none">{tp(key)}</span>
                  </h2>
                  {d.slots[key].length === 0 ? (
                    <p className="mt-4 text-ink-faint">{t("nothing")}</p>
                  ) : (
                    <ul className="mt-4 grid gap-3">
                      {d.slots[key].map((m) => <Row key={m.id} m={m} thumb={thumbs[m.id]} locale={locale} />)}
                    </ul>
                  )}
                </section>
              ))}
            </div>
            )}
            {d.as_needed.length > 0 && (
              <section aria-labelledby="as-needed" className="mt-5 break-inside-avoid rounded-card border border-dashed border-rule-strong p-5">
                <h2 id="as-needed" className="flex items-center gap-3 font-bn-display text-[24px]">
                  <Pill aria-hidden size={32} className="text-ink-soft" /> {tp("asNeeded")}
                </h2>
                <ul className="mt-3 grid gap-3">
                  {d.as_needed.map((m) => <Row key={m.id} m={m} thumb={thumbs[m.id]} locale={locale} />)}
                </ul>
              </section>
            )}
            <p className="mt-6 text-[15px] text-ink-faint">{t("fromPlan")}</p>
            {!ramadan && <RamadanRequest pid={pid} status={d.ramadan_status} onChange={today.reload} />}
          </>
        )}
      </main>
    </>
  );
}

function Row({ m, thumb, locale }: { m: TodayMedicine; thumb?: string; locale: string }) {
  const t = useTranslations("today");
  return (
    <li className="flex items-center gap-3">
      {thumb ? (
        // eslint-disable-next-line @next/next/no-img-element -- this phone's own photo, never uploaded or stored
        <img src={thumb} alt="" className="h-16 w-16 shrink-0 rounded-md border border-rule object-cover print:h-14 print:w-14" />
      ) : (
        <span aria-hidden className="foil h-16 w-16 shrink-0 rounded-md border border-foil-lo print:h-14 print:w-14 print:border-ink" />
      )}
      <span className="min-w-0 flex-1">
        <span className="block text-[20px] font-semibold leading-tight">{m.brand}</span>
        <span className="block text-base text-ink-soft">
          {m.generic ? genericName(m.generic, locale) : ""}{m.strength ? ` · ${m.strength}` : ""}
        </span>
        {(m.purpose_bn || m.purpose) && (
          <span className="block text-[15px] text-ink-soft">{locale === "bn" ? m.purpose_bn ?? m.purpose : m.purpose ?? m.purpose_bn}</span>
        )}
      </span>
      <Tablets n={m.per_dose} label={t("tablets", { count: m.per_dose })} />
    </li>
  );
}

/** The number of tablets drawn as tablets, so it can be read without reading numbers. */
function Tablets({ n, label }: { n: number; label: string }) {
  return (
    <span role="img" aria-label={label} className="flex shrink-0 flex-wrap justify-end gap-1">
      {Array.from({ length: Math.min(n, 6) }).map((_, i) => (
        <span key={i} className="h-6 w-6 rounded-full border-2 border-ink bg-paper shadow-[inset_0_-3px_0_rgb(0_0_0_/_0.12)]" />
      ))}
    </span>
  );
}

function ListenSchedule({ text }: { text: string }) {
  const t = useTranslations("today");
  const locale = useLocale();
  const voice = useVoice(locale === "bn" ? "bn" : "en");
  const [speaking, setSpeaking] = useState(false);
  if (!voice) return null; // no Bangla voice on this phone: no button that would read it wrong
  return (
    <button
      type="button"
      aria-pressed={speaking}
      onClick={() => {
        const synth = window.speechSynthesis;
        if (speaking) { synth.cancel(); setSpeaking(false); return; }
        const u = new SpeechSynthesisUtterance(text);
        u.voice = voice;
        u.lang = voice.lang;
        u.rate = 0.85;
        u.onend = u.onerror = () => setSpeaking(false);
        synth.cancel();
        synth.speak(u);
        setSpeaking(true);
      }}
      className={buttonStyles.primary.replace("w-full", "w-auto")}
    >
      <Volume2 aria-hidden size={22} /> {speaking ? t("stop") : t("listen")}
    </button>
  );
}

/** The family can ask for a fasting plan. Nothing changes until a pharmacist or doctor approves one. */
function RamadanRequest({ pid, status, onChange }: { pid: number; status: "requested" | "approved" | null; onChange: () => void }) {
  const t = useTranslations("today");
  const [busy, setBusy] = useState(false);
  return (
    <section aria-labelledby="ramadan-h" className="no-print mt-8 rounded-card border border-rule bg-paper-raised p-5">
      <h2 id="ramadan-h" className="flex items-center gap-2 font-semibold"><MoonStar aria-hidden size={20} className="text-neel" /> {t("ramadanTitle")}</h2>
      {status === "requested" ? (
        <p className="mt-2 text-ink-soft" role="status">{t("ramadanWaiting")}</p>
      ) : (
        <>
          <p className="mt-2 text-ink-soft">{t("ramadanBody")}</p>
          <button type="button" disabled={busy} className={cx(buttonStyles.secondary, "mt-3")}
            onClick={async () => { setBusy(true); try { await api.ramadanRequest(pid); onChange(); } finally { setBusy(false); } }}>
            <MoonStar aria-hidden size={18} /> {t("ramadanAsk")}
          </button>
        </>
      )}
    </section>
  );
}
