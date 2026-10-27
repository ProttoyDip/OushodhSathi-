"use client";

import { AlertTriangle, Moon, Phone, Pill, ShieldAlert, Sun, Sunrise } from "lucide-react";
import { useParams } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { DemoTag, LangToggle, ThemeToggle } from "@/components/Chrome";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { genericName, num } from "@/lib/format";
import type { Slot } from "@/lib/types";
import { useApi } from "@/lib/useApi";

const SLOT_ICON = { morning: Sunrise, noon: Sun, night: Moon } as const;

/** What the passport QR opens: read-only, no login, first name only. The family can switch it off. */
export default function EmergencyPage() {
  const { token } = useParams<{ token: string }>();
  const t = useTranslations("emergency");
  const tp = useTranslations("passport");
  const locale = useLocale();
  const page = useApi(() => api.emergency(token), [token]);
  const d = page.data;

  return (
    <div className="min-h-dvh text-[18px]">
      <header className="border-b-4 border-red bg-red-tint">
        <div className="mx-auto flex max-w-[720px] items-center justify-between gap-3 px-4 py-4">
          <h1 className="flex items-center gap-2 text-xl font-bold text-red">
            <ShieldAlert aria-hidden size={26} /> {t("title")}
          </h1>
          <div className="flex items-center gap-2"><ThemeToggle /><LangToggle /></div>
        </div>
      </header>
      <main className="mx-auto max-w-[720px] px-4 pb-16 pt-6">
        {page.error ? (
          page.error.status === 404 ? (
            <p role="alert" className="rounded-card border border-rule bg-paper-raised p-5 text-lg">{t("inactive")}</p>
          ) : (
            <ErrorState error={page.error} onRetry={page.reload} />
          )
        ) : !d ? (
          <Skeleton lines={4} />
        ) : (
          <div className="grid gap-6">
            {d.is_demo && <DemoTag />}
            <p className="font-bn-display text-[30px] leading-tight">
              {locale === "bn" ? d.first_name : d.first_name_en || d.first_name}
              <span className="tabular ml-3 text-xl text-ink-soft">{locale === "bn" ? `${num(d.age, locale)} বছর` : `${d.age} years`}</span>
            </p>

            <section aria-labelledby="allergy-h" className="rounded-card border-2 border-red bg-paper-raised p-5">
              <h2 id="allergy-h" className="flex items-center gap-2 font-semibold text-red"><AlertTriangle aria-hidden size={20} /> {t("allergies")}</h2>
              <p className="mt-2 text-2xl font-bold">{d.allergies.length ? d.allergies.join(", ") : <span className="text-lg font-normal text-ink-soft">{t("noAllergies")}</span>}</p>
              {d.allergies.length > 0 && !d.allergies_confirmed && <p className="mt-1 text-base text-ink-soft">{t("allergiesUnconfirmed")}</p>}
            </section>

            {d.emergency_contact && (
              <a href={`tel:${d.emergency_contact.phone.replace(/\s/g, "")}`} className="press flex min-h-16 items-center gap-3 rounded-card bg-neel px-5 text-lg font-semibold text-on-neel">
                <Phone aria-hidden size={24} />
                <span className="min-w-0">
                  <span className="block">{t("call", { name: d.emergency_contact.name ?? t("contact") })}</span>
                  <span className="tabular block text-base font-medium opacity-90">{d.emergency_contact.phone}</span>
                </span>
              </a>
            )}

            <section aria-labelledby="meds-h">
              <h2 id="meds-h" className="font-semibold">{t("medicines", { count: d.medicines.length })}</h2>
              <ul className="mt-3 grid gap-3">
                {d.medicines.map((m, i) => (
                  <li key={i} className="rounded-card border border-rule bg-paper-raised p-4">
                    <p className="flex flex-wrap items-baseline gap-x-2.5">
                      <span className="text-[22px] font-semibold">{m.generic ? genericName(m.generic, "en") : m.brand}</span>
                      {m.generic && <span lang="bn" className="text-ink-soft">{genericName(m.generic, "bn")}</span>}
                    </p>
                    <p className="tabular text-base text-ink-soft">{m.brand}{m.strength ? ` ${m.strength}` : ""}{m.per_dose > 1 ? ` × ${m.per_dose}` : ""}</p>
                    <p className="mt-2 flex flex-wrap items-center gap-2 text-base">
                      {m.schedule.length ? m.schedule.map((s: Slot) => {
                        const Icon = SLOT_ICON[s];
                        return <span key={s} className="inline-flex items-center gap-1 rounded-chip bg-paper-sunk px-3 py-1"><Icon aria-hidden size={16} /> {tp(s)}</span>;
                      }) : <span className="inline-flex items-center gap-1 rounded-chip bg-paper-sunk px-3 py-1"><Pill aria-hidden size={16} /> {tp("asNeeded")}</span>}
                      {(m.purpose_bn || m.purpose) && <span className="text-ink-soft">{tp("purpose")}: {locale === "bn" ? m.purpose_bn ?? m.purpose : m.purpose ?? m.purpose_bn}</span>}
                    </p>
                  </li>
                ))}
              </ul>
            </section>
            <p className="border-t border-rule pt-4 text-[15px] text-ink-faint">{t("footer")}</p>
          </div>
        )}
      </main>
    </div>
  );
}
