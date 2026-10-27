"use client";

import { Clock, Moon, Pill, Printer, Sun, Sunrise, Volume2 } from "lucide-react";
import { useParams } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { useVoice } from "@/components/sathi/speech";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { cx, genericName } from "@/lib/format";
import { reveal } from "@/lib/reveal";
import { loadThumbs } from "@/lib/thumbs";
import type { Slot, TodayMedicine } from "@/lib/types";
import { useApi } from "@/lib/useApi";

const SLOTS: { key: Slot; Icon: typeof Sun; tone: string }[] = [
  { key: "morning", Icon: Sunrise, tone: "text-amber" },
  { key: "noon", Icon: Sun, tone: "text-amber" },
  { key: "night", Icon: Moon, tone: "text-neel" },
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

  const spoken = d
    ? SLOTS.filter(({ key }) => d.slots[key].length).map(({ key }) => {
        const meds = d.slots[key].map((m) => (locale === "bn"
          ? `${m.brand} ${BN_COUNT[m.per_dose] ?? m.per_dose}`
          : `${m.brand}, ${EN_COUNT[m.per_dose] ?? `${m.per_dose} tablets`}`)).join(locale === "bn" ? ", " : "; ");
        return `${tp(key)}: ${meds}।`;
      }).join(" ")
    : "";

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
