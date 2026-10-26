"use client";

import { Moon, Pill, Sun, Sunrise } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import QRCode from "qrcode";
import { useEffect, useState } from "react";
import { cx, date, genericName, num } from "@/lib/format";
import type { Passport, PassportEntry } from "@/lib/types";
import { BrandMark } from "./BrandMark";
import { SeverityBadge } from "./SeverityBadge";

const SLOTS = [
  { key: "morning", Icon: Sunrise },
  { key: "noon", Icon: Sun },
  { key: "night", Icon: Moon },
  { key: "as_needed", Icon: Pill },
] as const;

const SLOT_MSG = { morning: "morning", noon: "noon", night: "night", as_needed: "asNeeded" } as const;

/**
 * A5 printable card. Generic names large (what any doctor reads), brand small
 * (what is printed on the strip). Must survive black-and-white printing.
 */
export function MedicinePassport({ passport, url }: { passport: Passport; url?: string }) {
  const t = useTranslations("passport");
  const locale = useLocale();
  const [qr, setQr] = useState<string | null>(null);
  const p = passport.patient;

  useEffect(() => {
    if (!url) return;
    QRCode.toString(url, { type: "svg", margin: 0, errorCorrectionLevel: "M", color: { dark: "#000000", light: "#ffffff" } })
      .then(setQr)
      .catch(() => setQr(null));
  }, [url]);

  const conditions = p.conditions.map((c) => (t.has(`conditions.${c}`) ? t(`conditions.${c}`) : c)).join(" · ");

  return (
    <article className="passport-card @container relative mx-auto w-full max-w-[148mm] overflow-hidden rounded-card border border-rule-strong bg-paper-raised text-ink shadow-soft print:max-w-none print:rounded-none print:border-0 print:shadow-none">
      {/* header */}
      {/* narrow card (phone): patient details stack under the title; wide card (desktop, A5 print): side by side */}
      <header className="flex flex-col gap-3 border-b-2 border-ink px-6 pb-4 pt-6 @md:flex-row @md:items-start @md:justify-between @md:gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-ink-soft">
            <BrandMark size={22} />
            <span lang="bn" className="font-bn-display text-[17px]">ওষুধসাথী</span>
          </div>
          <h1 lang="bn" className="mt-2 font-bn-display text-[34px] leading-[1.15]">ওষুধের পাসপোর্ট</h1>
          <p lang="en" className="font-display text-[22px] italic leading-tight text-ink-soft">Medicine passport</p>
        </div>
        <div className="min-w-0 break-words border-t border-rule pt-3 @md:max-w-[50%] @md:border-t-0 @md:pt-0 @md:text-right">
          {p.name_bn && <p lang="bn" className="font-bn-display text-[22px] leading-tight">{p.name_bn}</p>}
          <p lang="en" className="text-base font-semibold">{p.name}</p>
          <p className="tabular text-[15px] text-ink-soft">
            {locale === "bn" ? `${num(p.age, locale)} বছর` : `${p.age} years`}
            {p.district ? ` · ${p.district}` : ""}
          </p>
          {conditions && <p className="text-[15px] text-ink-soft">{conditions}</p>}
        </div>
      </header>

      {/* medicines by time of day */}
      <div className="px-6 py-5">
        {passport.medicine_count === 0 && <p className="text-lg text-ink-soft">{t("empty")}</p>}
        {SLOTS.map(({ key, Icon }) => {
          const entries = passport.groups[key];
          if (!entries?.length) return null;
          return (
            <section key={key} className="break-inside-avoid border-b border-rule py-3 last:border-b-0">
              <h2 className="flex items-baseline gap-2">
                <Icon aria-hidden size={18} className="translate-y-0.5 self-start text-ink-soft" />
                <span lang="bn" className="font-bn-display text-[22px] leading-none">{bnSlot(key)}</span>
                <span lang="en" className="font-display text-[17px] italic leading-none text-ink-soft">{t(`${SLOT_MSG[key]}En`)}</span>
              </h2>
              <ul className="mt-2 grid gap-2 pl-[26px]">
                {entries.map((e) => (
                  <Entry key={`${key}-${e.id}`} e={e} needsCheck={t("needsCheck")} />
                ))}
              </ul>
            </section>
          );
        })}
      </div>

      {/* confirmed notes */}
      <section className="break-inside-avoid border-t border-rule bg-paper-sunk/60 px-6 py-4 print:bg-transparent">
        <h2 className="text-[15px] font-semibold uppercase tracking-[0.06em] text-ink-soft">{t("notes")}</h2>
        {passport.confirmed_notes.length === 0 ? (
          <p className="mt-1 text-[15px] text-ink-soft">{t("noNotes")}</p>
        ) : (
          <ul className="mt-2 grid gap-2.5">
            {passport.confirmed_notes.map((n, i) => (
              <li key={i} className="grid grid-cols-[auto_1fr] items-start gap-x-3 text-[15px] leading-snug">
                <SeverityBadge severity={n.severity} size="sm" className="print:border-ink print:bg-transparent print:text-ink" />
                <div>
                  <span className="font-semibold">{n.brands.join(" + ")}</span>
                  {n.note && <span className="text-ink-soft"> — {n.note}</span>}
                  {n.reviewer && <span className="block text-[13px] text-ink-faint">{n.reviewer}{n.reviewed_at ? `, ${date(n.reviewed_at, locale)}` : ""}</span>}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* footer: QR + instruction */}
      <footer className="flex items-center justify-between gap-4 border-t-2 border-ink px-6 py-4">
        <div className="min-w-0">
          <p lang="bn" className="font-bn-display text-[20px] leading-snug">{t("showAtVisit")}</p>
          <p lang="en" className="font-display text-[18px] italic leading-snug text-ink-soft">{t("showAtVisitEn")}</p>
          <p className="mt-1 text-[13px] text-ink-faint">{t("updated", { date: date(passport.generated_at, locale) })}</p>
          {passport.demo_label && (
            <p className="mt-1 text-[13px] font-medium text-ink-soft">{passport.demo_label}</p>
          )}
        </div>
        <div className="shrink-0 text-center">
          <div
            className={cx("h-[92px] w-[92px] bg-white p-1.5", !qr && "animate-[breathe_1.6s_ease-in-out_infinite] bg-paper-sunk")}
            aria-label={t("scanQr")}
            role="img"
            dangerouslySetInnerHTML={qr ? { __html: qr } : undefined}
          />
          <p className="mt-1 max-w-[100px] text-[13px] leading-tight text-ink-faint">{t("scanQr")}</p>
        </div>
      </footer>
    </article>
  );
}

function bnSlot(key: string) {
  return { morning: "সকাল", noon: "দুপুর", night: "রাত", as_needed: "প্রয়োজনে" }[key] ?? key;
}

function Entry({ e, needsCheck }: { e: PassportEntry; needsCheck: string }) {
  const english = e.generic ? genericName(e.generic, "en") : e.brand;
  const bangla = e.generic ? genericName(e.generic, "bn") : null;
  return (
    <li className="flex flex-wrap items-baseline gap-x-2.5">
      <span className="text-[21px] font-semibold leading-tight">{english}</span>
      {bangla && <span lang="bn" className="text-[17px] text-ink-soft">{bangla}</span>}
      <span className="tabular text-[15px] text-ink-soft">
        {e.brand}
        {e.strength ? ` ${e.strength}` : ""}
        {e.prescriber ? ` · ${e.prescriber}` : ""}
      </span>
      {e.needs_review && (
        <span className="rounded-chip border border-dashed border-amber px-2 text-[13px] font-semibold text-amber print:border-ink print:text-ink">
          {needsCheck}
        </span>
      )}
    </li>
  );
}
