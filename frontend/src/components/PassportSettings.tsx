"use client";

import { Download, ExternalLink, Plus, RefreshCw, ShieldAlert, X } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { buttonStyles } from "@/components/Chrome";
import { api } from "@/lib/api";
import { cx } from "@/lib/format";
import type { Passport, Patient } from "@/lib/types";

/** What the family adds to the passport: allergies, an emergency contact, and the emergency page. */
export function PassportSettings({ pid, passport, patient, token, onToken, onChanged }: {
  pid: number;
  passport: Passport;
  patient?: Patient;
  token: string | null | undefined;
  onToken: (t: string | null) => void;
  onChanged: () => void;
}) {
  const t = useTranslations("passport");
  const tc = useTranslations("common");
  const [allergy, setAllergy] = useState("");
  const [name, setName] = useState(patient?.emergency_contact_name ?? "");
  const [phone, setPhone] = useState(patient?.emergency_contact_phone ?? "");
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const allergies = passport.allergies ?? [];
  const field = "mt-1 block h-12 w-full rounded-md border border-rule-strong bg-paper px-3 text-lg text-ink";

  async function run(fn: () => Promise<unknown>) {
    setState("saving");
    try {
      await fn();
      setState("saved");
      onChanged();
    } catch {
      setState("error");
    }
  }
  const saveAllergies = (list: string[]) => run(() => api.patchPatient(pid, { allergies: list }));

  async function downloadFhir() {
    const bundle = await api.fhir(pid);
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/fhir+json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `oushodhsathi-${pid}-fhir.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return (
    <section aria-labelledby="safety-h" className="no-print mt-8 grid gap-6 rounded-card border border-rule bg-paper-raised p-5">
      <div>
        <h2 id="safety-h" className="font-bn-display text-[24px] leading-tight">{t("safetyTitle")}</h2>
        <p className="mt-1 text-base text-ink-soft">{t("safetyIntro")}</p>
      </div>

      {/* allergies */}
      <div>
        <h3 className="font-semibold">{t("allergies")}</h3>
        <ul className="mt-2 flex flex-wrap gap-2">
          {allergies.map((a) => (
            <li key={a} className="inline-flex min-h-11 items-center gap-1 rounded-chip border border-rule-strong bg-paper pl-4 pr-1">
              {a}
              <button type="button" aria-label={t("removeAllergy", { name: a })} onClick={() => saveAllergies(allergies.filter((x) => x !== a))}
                className="inline-flex h-11 w-11 items-center justify-center rounded-full text-ink-soft hover:text-ink">
                <X aria-hidden size={16} />
              </button>
            </li>
          ))}
          {allergies.length === 0 && <li className="text-ink-soft">{t("allergiesNone")}</li>}
        </ul>
        <form
          className="mt-3 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            const a = allergy.trim();
            if (!a || allergies.includes(a)) return;
            setAllergy("");
            saveAllergies([...allergies, a]);
          }}
        >
          <label className="sr-only" htmlFor="allergy">{t("addAllergy")}</label>
          <input id="allergy" value={allergy} onChange={(e) => setAllergy(e.target.value)} maxLength={60}
            placeholder={t("allergyPh")} className="block h-12 min-w-0 flex-1 rounded-md border border-rule-strong bg-paper px-3 text-lg text-ink" />
          <button type="submit" disabled={!allergy.trim()} className={cx(buttonStyles.secondary, "shrink-0 px-4")}>
            <Plus aria-hidden size={18} /> {t("addAllergy")}
          </button>
        </form>
        {allergies.length > 0 && (
          <p className="mt-2 text-[15px] text-ink-faint">
            {passport.allergies_confirmed_by ? t("allergiesConfirmed", { name: passport.allergies_confirmed_by }) : t("allergiesUnconfirmed")}
          </p>
        )}
      </div>

      {/* emergency contact */}
      <form
        className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] sm:items-end"
        onSubmit={(e) => {
          e.preventDefault();
          run(() => api.patchPatient(pid, { emergency_contact_name: name.trim() || null, emergency_contact_phone: phone.trim() || null }));
        }}
      >
        <label className="text-base text-ink-soft">{t("contactName")}
          <input value={name} onChange={(e) => setName(e.target.value)} maxLength={80} className={field} autoComplete="off" />
        </label>
        <label className="text-base text-ink-soft">{t("contactPhone")}
          <input value={phone} onChange={(e) => setPhone(e.target.value.replace(/[^0-9+\- ]/g, ""))} maxLength={20}
            inputMode="tel" className={cx(field, "tabular")} autoComplete="off" />
        </label>
        <button type="submit" className={buttonStyles.secondary}>{t("saveContact")}</button>
      </form>

      {/* emergency page */}
      <div className="rounded-md border border-rule p-4">
        <h3 className="flex items-center gap-2 font-semibold"><ShieldAlert aria-hidden size={20} className="text-red" /> {t("emergencyTitle")}</h3>
        <p className="mt-1 text-base text-ink-soft">{t("emergencyBody")}</p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {token ? (
            <>
              <a href={`/e/${token}`} target="_blank" rel="noreferrer" className={cx(buttonStyles.quiet, "px-2")}>
                <ExternalLink aria-hidden size={18} /> {t("emergencyOpen")}
              </a>
              <button type="button" onClick={() => run(async () => onToken((await api.enableEmergency(pid)).token))} className={buttonStyles.quiet}>
                <RefreshCw aria-hidden size={18} /> {t("emergencyRenew")}
              </button>
              <button type="button" onClick={() => run(async () => { await api.revokeEmergency(pid); onToken(null); })} className={cx(buttonStyles.secondary, "text-red")}>
                {t("emergencyOff")}
              </button>
            </>
          ) : (
            <button type="button" onClick={() => run(async () => onToken((await api.enableEmergency(pid)).token))} className={buttonStyles.secondary}>
              {t("emergencyOn")}
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-rule pt-4">
        <p className="max-w-[52ch] text-[15px] text-ink-soft">{t("fhirHint")}</p>
        <button type="button" onClick={() => downloadFhir().catch(() => setState("error"))} className={buttonStyles.quiet}>
          <Download aria-hidden size={18} /> {t("fhirDownload")}
        </button>
      </div>
      <p className={cx("min-h-6 text-[15px]", state === "error" ? "text-red" : "text-ink-soft")} aria-live="polite">
        {state === "saved" ? t("saved") : state === "error" ? tc("errorGeneric") : ""}
      </p>
    </section>
  );
}
