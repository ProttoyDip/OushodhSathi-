"use client";

import { AlertTriangle, CalendarCheck, Check, Pill } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { api } from "@/lib/api";
import { cx, genericName } from "@/lib/format";
import type { MedicineItem, Patient } from "@/lib/types";

const head = "flex items-center gap-1.5 text-[13px] font-semibold uppercase tracking-[0.06em] text-ink-faint";

/** The reviewer's own entries: what each medicine is for, stopped, approved times, allergies.
 * Written by the pharmacist or doctor; nothing here is generated. */
export function ClinicalEditor({ token, reviewer, patient, items, onChanged }: {
  token: string;
  reviewer: string;
  patient: Patient;
  items: MedicineItem[];
  onChanged: () => void;
}) {
  const t = useTranslations("review.clinical");
  const ts = useTranslations("passport");
  const locale = useLocale();
  const [busy, setBusy] = useState<string | null>(null);
  const confirmed = items.filter((i) => i.confirmed && !i.set_aside);
  const unapproved = confirmed.filter((i) => !i.stopped && i.schedule.length && !i.schedule_approved_at).length;
  const allergies = patient.allergies ?? [];

  async function act(key: string, fn: () => Promise<unknown>) {
    setBusy(key);
    try {
      await fn();
      onChanged();
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <section>
        <h3 className={head}><AlertTriangle aria-hidden size={14} /> {t("allergies")}</h3>
        <p className="mt-1.5 text-sm text-ink">{allergies.length ? allergies.join(", ") : <span className="text-ink-faint">{t("noAllergies")}</span>}</p>
        {allergies.length > 0 && (patient.allergies_confirmed_by ? (
          <p className="text-[13px] text-ink-faint">{t("confirmedBy", { name: patient.allergies_confirmed_by })}</p>
        ) : (
          <button type="button" disabled={busy === "allergies"} onClick={() => act("allergies", () => api.confirmAllergies(token, patient.id, reviewer))}
            className="mt-2 inline-flex h-9 items-center gap-1.5 rounded-md border border-neel px-3 text-sm font-semibold text-neel hover:bg-neel-tint">
            <Check aria-hidden size={15} /> {t("confirmAllergies")}
          </button>
        ))}
      </section>

      <section>
        <h3 className={head}><Pill aria-hidden size={14} /> {t("medicines", { n: confirmed.length })}</h3>
        <ul className="mt-2 grid gap-3 text-sm">
          {confirmed.map((i) => (
            <Med key={i.id} item={i} token={token} reviewer={reviewer} locale={locale} onChanged={onChanged} slotName={(s) => ts(s)} />
          ))}
        </ul>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button type="button" disabled={!unapproved || busy === "times"} onClick={() => act("times", () => api.approveSchedule(token, patient.id, reviewer))}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-neel px-3 text-sm font-semibold text-neel hover:bg-neel-tint disabled:border-rule disabled:text-ink-faint">
            <CalendarCheck aria-hidden size={15} /> {unapproved ? t("approveTimes", { n: unapproved }) : t("timesApproved")}
          </button>
        </div>
      </section>
    </>
  );
}

function Med({ item, token, reviewer, locale, onChanged, slotName }: {
  item: MedicineItem; token: string; reviewer: string; locale: string; onChanged: () => void; slotName: (s: string) => string;
}) {
  const t = useTranslations("review.clinical");
  const [purpose, setPurpose] = useState(item.purpose_bn ?? "");
  const [saving, setSaving] = useState(false);
  const save = async (body: { purpose_bn?: string | null; stopped?: boolean }) => {
    setSaving(true);
    try {
      await api.clinical(token, item.id, { ...body, reviewer });
      onChanged();
    } finally {
      setSaving(false);
    }
  };
  return (
    <li className={cx("rounded-md border border-rule p-2.5", item.stopped && "opacity-70")}>
      <p className="flex items-baseline justify-between gap-2">
        <span className={cx("font-medium text-ink", item.stopped && "line-through")}>{item.brand} <span className="tabular font-normal text-ink-soft">{item.strength}</span></span>
        <span className="truncate text-ink-soft">{item.generic ? genericName(item.generic, locale) : t("unknown")}</span>
      </p>
      <p className="text-[13px] text-ink-faint">
        {item.schedule.length ? item.schedule.map(slotName).join(" · ") : slotName("asNeeded")}
        {item.schedule.length > 0 && (item.schedule_approved_at ? ` · ${t("approved")}` : ` · ${t("notApproved")}`)}
      </p>
      <form className="mt-1.5 flex gap-1.5" onSubmit={(e) => { e.preventDefault(); save({ purpose_bn: purpose.trim() || null }); }}>
        <label className="sr-only" htmlFor={`purpose-${item.id}`}>{t("purposeLabel", { brand: item.brand })}</label>
        <input id={`purpose-${item.id}`} lang="bn" value={purpose} onChange={(e) => setPurpose(e.target.value)} maxLength={120}
          placeholder={t("purposePh")} className="h-9 min-w-0 flex-1 rounded-md border border-rule-strong bg-paper px-2 text-sm text-ink" />
        <button type="submit" disabled={saving || purpose === (item.purpose_bn ?? "")} className="h-9 rounded-md border border-rule-strong px-2.5 text-sm font-medium text-ink disabled:text-ink-faint">
          {t("save")}
        </button>
      </form>
      <label className="mt-1.5 flex min-h-9 items-center gap-2 text-[13px] text-ink-soft">
        <input type="checkbox" checked={!!item.stopped} disabled={saving} onChange={(e) => save({ stopped: e.target.checked })} className="h-4 w-4 accent-[var(--red)]" />
        {item.stopped ? t("stoppedBy", { name: item.stopped_by ?? "" }) : t("markStopped")}
      </label>
    </li>
  );
}
