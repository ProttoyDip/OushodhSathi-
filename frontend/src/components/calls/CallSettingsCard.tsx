"use client";

import { Check, PhoneCall } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { buttonStyles } from "@/components/Chrome";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";

/** Turn the daily Bangla check-in call on (with consent), pick its time, or stop it at any time. */
export function CallSettingsCard({ pid }: { pid: number }) {
  const t = useTranslations("calls.settings");
  const s = useApi(() => api.callSettings(pid), [pid]);
  const [time, setTime] = useState<string | null>(null);
  const [who, setWho] = useState("");
  const [phone, setPhone] = useState("");
  const [agree, setAgree] = useState(false);
  const [channel, setChannel] = useState<"call" | "whatsapp" | null>(null);
  const [state, setState] = useState<"idle" | "busy" | "saved">("idle");
  const [error, setError] = useState<string | null>(null);
  if (!s.data) return null;
  const d = s.data;
  const localTime = time ?? d.local_time ?? "19:30";
  const ch = channel ?? d.channel ?? "call";
  const needsPhone = ch === "whatsapp" ? d.whatsapp_live : d.needs_phone;
  const canSave = agree && who.trim().length > 0 && (!needsPhone || phone.trim() || d.phone);

  async function save() {
    setState("busy"); setError(null);
    try {
      await api.saveCallSettings(pid, { local_time: localTime, consent: true, consent_by: who.trim(), phone: phone.trim() || null, channel: ch });
      setState("saved"); setPhone(""); s.reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e)); setState("idle");
    }
  }

  async function stop() {
    setState("busy");
    try { await api.stopCalls(pid); s.reload(); } finally { setState("idle"); }
  }

  return (
    <section id="calls" className="rounded-card border border-rule bg-paper p-5">
      <h2 className="flex items-center gap-2 text-xl font-semibold text-ink">
        <PhoneCall aria-hidden size={22} className="text-neel" /> {t("title")}
      </h2>
      <div className="mt-3 grid gap-3 text-base text-ink-soft">
        <p>{t("body")}</p>
        {d.approved_slots.length === 0 && <p className="text-amber">{t("noTimes")}</p>}
        {d.active ? (
          <>
            <p className="font-semibold text-green">{t(d.channel === "whatsapp" ? "onWhatsapp" : "on", { time: d.local_time ?? "" })}{d.phone ? ` · ${d.phone}` : ""}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <Link href={`/p/${pid}/call`} className={buttonStyles.primary}>{t("try")}</Link>
              <button type="button" onClick={stop} disabled={state === "busy"} className={buttonStyles.secondary}>{t("stop")}</button>
            </div>
          </>
        ) : (
          <>
            <div role="radiogroup" aria-label={t("channel")} className="grid grid-cols-2 gap-3">
              {(["call", "whatsapp"] as const).map((v) => (
                <button key={v} type="button" role="radio" aria-checked={ch === v} onClick={() => setChannel(v)}
                  className={`press inline-flex min-h-12 items-center justify-center rounded-card border px-3 text-base font-semibold ${
                    ch === v ? "border-neel bg-neel-tint text-neel" : "border-rule-strong text-ink-soft hover:bg-paper-sunk"}`}>
                  {t(v === "call" ? "channelCall" : "channelWhatsapp")}
                </button>
              ))}
            </div>
            <label className="grid gap-1 text-ink">
              {t("time")}
              <input type="time" min="08:00" max="20:45" value={localTime} onChange={(e) => setTime(e.target.value)}
                className="block h-12 w-full rounded-md border border-rule-strong bg-paper-raised px-3 text-lg text-ink" />
            </label>
            <label className="grid gap-1 text-ink">
              {t("who")}
              <input type="text" maxLength={60} value={who} onChange={(e) => setWho(e.target.value)} placeholder={t("whoHint")}
                className="block h-12 w-full rounded-md border border-rule-strong bg-paper-raised px-3 text-lg text-ink" />
            </label>
            {needsPhone && (
              <label className="grid gap-1 text-ink">
                {t("phone")}
                <input type="tel" inputMode="tel" maxLength={20} value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="01XXXXXXXXX"
                  className="block h-12 w-full rounded-md border border-rule-strong bg-paper-raised px-3 text-lg text-ink" />
              </label>
            )}
            <p className="rounded-md bg-paper-sunk p-3 text-[15px]">{ch === "whatsapp" ? (d.whatsapp_live ? t("consentWhatsapp") : t("consentWhatsappSim")) : d.needs_phone ? t("consentPhone") : t("consentSim")}</p>
            <label className="flex min-h-12 cursor-pointer items-start gap-3 text-ink">
              <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} className="mt-0.5 h-6 w-6 shrink-0 accent-[var(--neel)]" />
              <span>{t("agree")}</span>
            </label>
            <button type="button" onClick={save} disabled={!canSave || state === "busy"} className={buttonStyles.primary}>
              {state === "saved" ? <><Check aria-hidden size={18} /> {t("saved")}</> : t("turnOn")}
            </button>
          </>
        )}
        {error && <p role="alert" className="text-red">{error}</p>}
      </div>
    </section>
  );
}
