"use client";

import { ArrowLeft, Check, Copy, KeyRound, LogOut, RotateCcw, ShieldOff, UserPlus } from "lucide-react";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useCallback, useEffect, useState } from "react";
import { Wordmark } from "@/components/BrandMark";
import { LangToggle, ThemeToggle } from "@/components/Chrome";
import { api, ApiError } from "@/lib/api";
import { cx, date } from "@/lib/format";
import type { ReviewerAccount } from "@/lib/types";

const SESSION = "oushodh:admin";
const field = "mt-1.5 block h-11 w-full rounded-md border border-rule-strong bg-paper px-3 text-base text-ink";
const button = "press inline-flex h-11 items-center justify-center gap-2 rounded-card px-4 font-semibold transition-colors disabled:opacity-60";

/** For the team only: personal reviewer invites, revoking them, and re-issuing a lost family link.
 * The admin token lives in this tab's sessionStorage and is sent as X-Admin-Token. */
export default function AdminPage() {
  const t = useTranslations("admin");
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    try { setToken(sessionStorage.getItem(SESSION)); } catch {}
    setReady(true);
  }, []);
  if (!ready) return null;

  return (
    <main className="mx-auto min-h-dvh max-w-[880px] px-6 py-10">
      <div className="mb-8 flex items-center justify-between gap-2">
        <Link href="/" className="-ml-2 inline-flex h-11 items-center gap-1.5 rounded-chip px-2 font-medium text-ink-soft hover:text-ink">
          <ArrowLeft aria-hidden size={18} /> <Wordmark />
        </Link>
        <div className="flex items-center gap-2">
          {token && (
            <button type="button" onClick={() => { try { sessionStorage.removeItem(SESSION); } catch {} setToken(null); }}
              className="inline-flex h-11 items-center gap-1.5 rounded-chip border border-rule px-3 text-sm font-medium text-ink-soft hover:text-ink">
              <LogOut aria-hidden size={16} /> {t("signOut")}
            </button>
          )}
          <ThemeToggle className="h-11 w-11" />
          <LangToggle className="h-11" />
        </div>
      </div>
      <h1 className="font-display text-[36px] leading-[1.1] text-ink">{t("title")}</h1>
      <p className="mt-2 max-w-[60ch] text-ink-soft">{t("body")}</p>
      {token ? <Panel token={token} /> : (
        <SignIn onSignIn={(v) => { try { sessionStorage.setItem(SESSION, v); } catch {} setToken(v); }} />
      )}
    </main>
  );
}

function SignIn({ onSignIn }: { onSignIn: (token: string) => void }) {
  const t = useTranslations("admin");
  const [value, setValue] = useState("");
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);
  return (
    <form className="mt-8 grid max-w-[420px] gap-4" onSubmit={async (e) => {
      e.preventDefault();
      setBusy(true);
      setError(undefined);
      try {
        await api.admin.reviewers(value.trim());
        onSignIn(value.trim());
      } catch (err) {
        setError(err instanceof ApiError && err.status === 401 ? t("badToken")
          : err instanceof ApiError && err.status === 503 ? t("notConfigured") : t("offline"));
      } finally {
        setBusy(false);
      }
    }}>
      <label className="text-sm font-medium text-ink-soft">
        {t("token")}
        <input required type="password" value={value} onChange={(e) => setValue(e.target.value)} className={field} autoComplete="current-password" />
      </label>
      {error && <p role="alert" className="rounded-md border border-red-line bg-red-tint px-3 py-2 text-red">{error}</p>}
      <button type="submit" disabled={busy} className={cx(button, "bg-neel text-on-neel hover:bg-neel-hover")}>
        <KeyRound aria-hidden size={18} /> {t("open")}
      </button>
    </form>
  );
}

function Panel({ token }: { token: string }) {
  const t = useTranslations("admin");
  const locale = useLocale();
  const [rows, setRows] = useState<ReviewerAccount[]>([]);
  const [invite, setInvite] = useState<{ name: string; url: string } | null>(null);
  const [error, setError] = useState(false);
  const load = useCallback(() => api.admin.reviewers(token).then(setRows).catch(() => setError(true)), [token]);
  useEffect(() => { load(); }, [load]);

  async function act(fn: () => Promise<unknown>) {
    setError(false);
    try { await fn(); await load(); } catch { setError(true); }
  }

  return (
    <div className="mt-8 grid gap-8">
      {invite && <OneTimeLink label={t("inviteFor", { name: invite.name })} url={invite.url} onDone={() => setInvite(null)} />}
      <NewReviewer token={token} onCreated={(name, url) => { setInvite({ name, url }); load(); }} />

      <section>
        <h2 className="text-xl font-semibold text-ink">{t("reviewers")}</h2>
        {rows.length === 0 ? <p className="mt-2 text-ink-soft">{t("none")}</p> : (
          <ul className="mt-3 divide-y divide-rule rounded-card border border-rule">
            {rows.map((r) => (
              <li key={r.id} className="flex flex-wrap items-center gap-3 px-4 py-3">
                <span className="min-w-0 flex-1">
                  <span className={cx("block font-semibold", r.revoked_at ? "text-ink-faint line-through" : "text-ink")}>{r.name}</span>
                  <span className="block text-sm text-ink-soft">
                    {t(`role.${r.role}`)}{r.reg_no ? ` · ${r.reg_no}` : ""} · {date(r.created_at, locale, { day: "numeric", month: "short", year: "numeric" })}
                    {r.revoked_at && ` · ${t("revoked")}`}
                  </span>
                </span>
                <button type="button" onClick={() => act(async () => {
                  const inv = await api.admin.reissue(token, r.id);
                  setInvite({ name: inv.name, url: inv.invite_url });
                })} className={cx(button, "border border-rule text-ink-soft hover:text-ink")}>
                  <RotateCcw aria-hidden size={16} /> {t("reissue")}
                </button>
                {!r.revoked_at && (
                  <button type="button" onClick={() => act(() => api.admin.revoke(token, r.id))}
                    className={cx(button, "border border-red-line text-red hover:bg-red-tint")}>
                    <ShieldOff aria-hidden size={16} /> {t("revoke")}
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <FamilyLink token={token} />
      {error && <p role="alert" className="text-red">{t("error")}</p>}
    </div>
  );
}

function NewReviewer({ token, onCreated }: { token: string; onCreated: (name: string, url: string) => void }) {
  const t = useTranslations("admin");
  const [name, setName] = useState("");
  const [role, setRole] = useState<"pharmacist" | "doctor">("pharmacist");
  const [reg, setReg] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <form className="grid gap-4 rounded-card border border-rule bg-paper p-5 sm:grid-cols-[1fr_auto_1fr_auto] sm:items-end"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        try {
          const inv = await api.admin.createReviewer(token, { name: name.trim(), role, reg_no: reg.trim() || null });
          onCreated(inv.name, inv.invite_url);
          setName(""); setReg("");
        } finally {
          setBusy(false);
        }
      }}>
      <label className="text-sm font-medium text-ink-soft">
        {t("name")}
        <input required minLength={2} maxLength={80} value={name} onChange={(e) => setName(e.target.value)} className={field} placeholder={t("namePh")} />
      </label>
      <label className="text-sm font-medium text-ink-soft">
        {t("roleLabel")}
        <select value={role} onChange={(e) => setRole(e.target.value as "pharmacist" | "doctor")} className={field}>
          <option value="pharmacist">{t("role.pharmacist")}</option>
          <option value="doctor">{t("role.doctor")}</option>
        </select>
      </label>
      <label className="text-sm font-medium text-ink-soft">
        {t("reg")}
        <input maxLength={40} value={reg} onChange={(e) => setReg(e.target.value)} className={field} placeholder={t("regPh")} />
      </label>
      <button type="submit" disabled={busy} className={cx(button, "bg-neel text-on-neel hover:bg-neel-hover")}>
        <UserPlus aria-hidden size={18} /> {t("create")}
      </button>
    </form>
  );
}

function FamilyLink({ token }: { token: string }) {
  const t = useTranslations("admin");
  const [pid, setPid] = useState("");
  const [link, setLink] = useState<string>();
  const [error, setError] = useState(false);
  return (
    <section>
      <h2 className="text-xl font-semibold text-ink">{t("familyTitle")}</h2>
      <p className="mt-1 text-ink-soft">{t("familyBody")}</p>
      <form className="mt-3 flex flex-wrap items-end gap-3" onSubmit={async (e) => {
        e.preventDefault();
        setError(false);
        try { setLink((await api.admin.familyLink(token, Number(pid))).family_url); } catch { setError(true); }
      }}>
        <label className="text-sm font-medium text-ink-soft">
          {t("household")}
          <input required type="number" min={1} value={pid} onChange={(e) => setPid(e.target.value)} className={cx(field, "w-40 tabular")} />
        </label>
        <button type="submit" className={cx(button, "border border-rule-strong text-ink hover:border-ink-faint")}>{t("familyButton")}</button>
      </form>
      {error && <p role="alert" className="mt-2 text-red">{t("error")}</p>}
      {link && <div className="mt-4"><OneTimeLink label={t("familyNew")} url={link} onDone={() => setLink(undefined)} /></div>}
    </section>
  );
}

/** Shown once: the server never returns this token again. */
function OneTimeLink({ label, url, onDone }: { label: string; url: string; onDone: () => void }) {
  const t = useTranslations("admin");
  const [copied, setCopied] = useState(false);
  return (
    <div role="status" className="rounded-card border border-neel bg-neel-tint p-4">
      <p className="font-semibold text-ink">{label}</p>
      <p className="mt-1 break-all font-mono text-sm text-ink" translate="no">{url}</p>
      <p className="mt-2 text-sm text-ink-soft">{t("onceWarning")}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" onClick={async () => { try { await navigator.clipboard.writeText(url); setCopied(true); } catch {} }}
          className={cx(button, "border border-rule-strong bg-paper text-ink")}>
          {copied ? <Check aria-hidden size={16} /> : <Copy aria-hidden size={16} />} {copied ? t("copied") : t("copy")}
        </button>
        <button type="button" onClick={onDone} className={cx(button, "text-ink-soft hover:text-ink")}>{t("done")}</button>
      </div>
    </div>
  );
}
