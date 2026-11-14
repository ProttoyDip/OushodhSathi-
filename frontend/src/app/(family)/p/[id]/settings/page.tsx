"use client";

import { Check, Download, KeyRound, Mail, Trash2, UserRound } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { forgetFamilyKey, rememberFamilyKey } from "@/lib/familyKey";
import { cx } from "@/lib/format";
import { reveal } from "@/lib/reveal";
import { useApi } from "@/lib/useApi";

const EMAIL = /^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,}$/;

/** The family's own controls: email, the private link, a copy of the data, and deleting it all. */
export default function SettingsPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const t = useTranslations("settings");
  const patient = useApi(() => api.patient(pid), [pid]);

  return (
    <>
      <FamilyHeader back={`/p/${pid}`} />
      <main className={`mx-auto w-full px-4 pb-16 pt-4 lg:pt-8 ${familyWidth}`}>
        <h1 {...reveal(0)} className="font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t("title")}</h1>
        {patient.error ? (
          <ErrorState error={patient.error} onRetry={patient.reload} />
        ) : !patient.data ? (
          <Skeleton />
        ) : patient.data.is_demo ? (
          <p className="mt-4 text-ink-soft">{t("demo")}</p>
        ) : (
          <div className="mt-6 grid max-w-[640px] gap-6">
            <EmailCard pid={pid} email={patient.data.family_email ?? ""} optIn={!!patient.data.email_opt_in} />
            <SexCard pid={pid} sex={patient.data.sex ?? null} />
            <LinkCard pid={pid} />
            <ExportCard pid={pid} />
            <DeleteCard pid={pid} />
          </div>
        )}
      </main>
    </>
  );
}

function Card({ Icon, title, children, danger }: { Icon: typeof Mail; title: string; children: React.ReactNode; danger?: boolean }) {
  return (
    <section className={cx("rounded-card border bg-paper p-5", danger ? "border-red-line" : "border-rule")}>
      <h2 className={cx("flex items-center gap-2 text-xl font-semibold", danger ? "text-red" : "text-ink")}>
        <Icon aria-hidden size={22} className={danger ? "text-red" : "text-neel"} /> {title}
      </h2>
      <div className="mt-3 grid gap-3 text-base text-ink-soft">{children}</div>
    </section>
  );
}

function EmailCard({ pid, email: initial, optIn: initialOptIn }: { pid: number; email: string; optIn: boolean }) {
  const t = useTranslations("settings.email");
  const [email, setEmail] = useState(initial);
  const [optIn, setOptIn] = useState(initialOptIn);
  const [state, setState] = useState<"idle" | "busy" | "saved" | "error">("idle");
  const ok = !email.trim() || EMAIL.test(email.trim());

  async function save() {
    setState("busy");
    try {
      await api.patchPatient(pid, { family_email: email.trim() || null, email_opt_in: !!email.trim() && optIn });
      setState("saved");
    } catch {
      setState("error");
    }
  }

  return (
    <Card Icon={Mail} title={t("title")}>
      <p>{t("body")}</p>
      <input type="email" inputMode="email" maxLength={254} value={email} aria-label={t("title")}
        onChange={(e) => { setEmail(e.target.value); setState("idle"); }}
        className="block h-12 w-full rounded-md border border-rule-strong bg-paper-raised px-3 text-lg text-ink" aria-invalid={!ok} />
      <label className="flex min-h-12 cursor-pointer items-start gap-3 text-ink">
        <input type="checkbox" checked={optIn && !!email.trim()} disabled={!email.trim()}
          onChange={(e) => { setOptIn(e.target.checked); setState("idle"); }}
          className="mt-0.5 h-6 w-6 shrink-0 accent-[var(--neel)]" />
        <span>{t("optIn")}</span>
      </label>
      <button type="button" disabled={!ok || state === "busy"} onClick={save} className={buttonStyles.secondary}>
        {state === "saved" ? <><Check aria-hidden size={18} /> {t("saved")}</> : t("save")}
      </button>
      {state === "error" && <p role="alert" className="text-red">{t("error")}</p>}
    </Card>
  );
}

/** Sex is used only to work out kidney function (eGFR) from a blood test. Optional. */
function SexCard({ pid, sex: initial }: { pid: number; sex: "female" | "male" | null }) {
  const t = useTranslations("settings.sex");
  const [sex, setSex] = useState(initial);
  const [state, setState] = useState<"idle" | "saved" | "error">("idle");

  async function choose(value: "female" | "male") {
    setSex(value);
    try {
      await api.patchPatient(pid, { sex: value });
      setState("saved");
    } catch {
      setState("error");
    }
  }

  return (
    <Card Icon={UserRound} title={t("title")}>
      <p>{t("body")}</p>
      <div role="radiogroup" aria-label={t("title")} className="grid grid-cols-2 gap-3">
        {(["female", "male"] as const).map((v) => (
          <button key={v} type="button" role="radio" aria-checked={sex === v} onClick={() => choose(v)}
            className={cx("press inline-flex min-h-12 items-center justify-center gap-2 rounded-card border px-4 text-base font-semibold",
              sex === v ? "border-neel bg-neel-tint text-neel" : "border-rule-strong text-ink-soft hover:bg-paper-sunk")}>
            {sex === v && <Check aria-hidden size={18} />} {t(v)}
          </button>
        ))}
      </div>
      {state === "saved" && <p className="text-green" aria-live="polite">{t("saved")}</p>}
      {state === "error" && <p role="alert" className="text-red">{t("error")}</p>}
    </Card>
  );
}

function LinkCard({ pid }: { pid: number }) {
  const t = useTranslations("settings.link");
  const [confirming, setConfirming] = useState(false);
  const [link, setLink] = useState<string>();
  const [error, setError] = useState(false);

  async function rotate() {
    setError(false);
    try {
      const { family_key } = await api.rotateFamilyKey(pid);
      rememberFamilyKey(pid, family_key);
      setLink(`${window.location.origin}/p/${pid}?key=${encodeURIComponent(family_key)}`);
      setConfirming(false);
    } catch {
      setError(true);
    }
  }

  return (
    <Card Icon={KeyRound} title={t("title")}>
      <p>{t("body")}</p>
      {link ? (
        <div className="rounded-md border border-rule bg-paper-raised p-3">
          <p className="font-semibold text-ink">{t("newLink")}</p>
          <p className="mt-1 break-all font-mono text-[15px] text-ink" translate="no">{link}</p>
        </div>
      ) : confirming ? (
        <div className="grid gap-2 sm:grid-cols-2">
          <button type="button" onClick={rotate} className={buttonStyles.secondary}>{t("confirm")}</button>
          <button type="button" onClick={() => setConfirming(false)} className={buttonStyles.quiet}>{t("cancel")}</button>
        </div>
      ) : (
        <button type="button" onClick={() => setConfirming(true)} className={buttonStyles.secondary}>{t("rotate")}</button>
      )}
      {error && <p role="alert" className="text-red">{t("error")}</p>}
    </Card>
  );
}

function ExportCard({ pid }: { pid: number }) {
  const t = useTranslations("settings.export");
  const [busy, setBusy] = useState(false);

  async function download() {
    setBusy(true);
    try {
      const data = await api.exportHousehold(pid);
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
      const a = Object.assign(document.createElement("a"), { href: url, download: `oushodhsathi-${pid}.json` });
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card Icon={Download} title={t("title")}>
      <p>{t("body")}</p>
      <button type="button" disabled={busy} onClick={download} className={buttonStyles.secondary}>
        <Download aria-hidden size={18} /> {t("download")}
      </button>
    </Card>
  );
}

function DeleteCard({ pid }: { pid: number }) {
  const t = useTranslations("settings.delete");
  const router = useRouter();
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const word = t("word");
  useEffect(() => setError(false), [typed]);

  async function remove() {
    setBusy(true);
    try {
      await api.deleteHousehold(pid);
      forgetFamilyKey(pid);
      router.replace("/?deleted=1");
    } catch {
      setBusy(false);
      setError(true);
    }
  }

  return (
    <Card Icon={Trash2} title={t("title")} danger>
      <p>{t("body")}</p>
      <label className="text-ink">
        {t.rich("type", { word, b: (c) => <strong className="font-semibold">{c}</strong> })}
        <input value={typed} onChange={(e) => setTyped(e.target.value)} autoComplete="off"
          className="mt-1 block h-12 w-full rounded-md border border-rule-strong bg-paper-raised px-3 text-lg text-ink" />
      </label>
      <button type="button" disabled={typed.trim() !== word || busy} onClick={remove}
        className="press inline-flex min-h-12 items-center justify-center gap-2 rounded-card bg-red px-5 text-base font-semibold text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-40">
        <Trash2 aria-hidden size={18} /> {t("button")}
      </button>
      {error && <p role="alert" className="text-red">{t("error")}</p>}
    </Card>
  );
}
