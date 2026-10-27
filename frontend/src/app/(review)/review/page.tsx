"use client";

import {
  ArrowLeft, Check, CircleCheck, Cpu, ExternalLink, FileText, History, KeyRound, LogOut, NotebookPen, Stethoscope, Undo2, X,
} from "lucide-react";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BrandMark, Wordmark } from "@/components/BrandMark";
import { DemoTag, LangToggle, ThemeToggle } from "@/components/Chrome";
import { DuplicateConnector } from "@/components/DuplicateConnector";
import { ReviewRow, useRuleName } from "@/components/ReviewRow";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StripCard } from "@/components/StripCard";
import { api, ApiError } from "@/lib/api";
import { cx, date, genericName, since } from "@/lib/format";
import type { AuditEntry, Flag, ReviewQueue } from "@/lib/types";
import { REVIEWER_SESSION, type ReviewerSession } from "@/lib/reviewer";
import { useApi } from "@/lib/useApi";
import { JudgeBar } from "@/components/JudgeBar";
import { CaseSummaryPanel } from "@/components/review/CaseSummaryPanel";
import { ClinicalEditor } from "@/components/review/ClinicalEditor";
import { QuestionsBoard } from "@/components/review/QuestionsBoard";

const SESSION = REVIEWER_SESSION;

type Session = ReviewerSession;
type Toast = { flag: Flag; status: "confirmed" | "dismissed"; until: number };

export default function ReviewPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    try {
      const s = sessionStorage.getItem(SESSION);
      if (s) setSession(JSON.parse(s));
    } catch {}
    setReady(true);
  }, []);
  if (!ready) return null;
  return session ? (
    <Dashboard session={session} onSignOut={() => { sessionStorage.removeItem(SESSION); setSession(null); }} />
  ) : (
    <Login onSignIn={(s) => { sessionStorage.setItem(SESSION, JSON.stringify(s)); setSession(s); }} />
  );
}

/* ------------------------------------------------------------------ login */

function Login({ onSignIn }: { onSignIn: (s: Session) => void }) {
  const health = useApi(() => api.health(), []);
  const t = useTranslations("review");
  const [name, setName] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);
  const field = "mt-1.5 block h-11 w-full rounded-md border border-rule-strong bg-paper px-3 text-base text-ink";

  return (
    <main className="mx-auto flex min-h-dvh max-w-[420px] flex-col justify-center px-6 py-12">
      <div className="mb-6 flex items-center justify-between gap-2">
        <Link href="/" className="-ml-2 inline-flex h-11 w-fit items-center gap-1.5 rounded-chip px-2 text-[15px] font-medium text-ink-soft hover:text-ink">
          <ArrowLeft aria-hidden size={18} /> {t("backToSite")}
        </Link>
        <div className="flex items-center gap-2">
          <ThemeToggle className="h-11 w-11" />
          <LangToggle className="h-11" />
        </div>
      </div>
      <Link href="/" title={t("home")} className="w-fit rounded-md"><Wordmark /></Link>
      <h1 className="mt-8 font-display text-[40px] leading-[1.1] text-ink">{t("login.title")}</h1>
      <p className="mt-2 text-ink-soft">{t("login.body")}</p>
      <form
        className="mt-8 grid gap-4"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError(undefined);
          try {
            await api.queue(token.trim());
            onSignIn({ token: token.trim(), name: name.trim() });
          } catch (err) {
            setError(err instanceof ApiError && err.status === 401 ? t("login.badToken") : t("login.offline"));
          } finally {
            setBusy(false);
          }
        }}
      >
        <label className="text-sm font-medium text-ink-soft">
          {t("login.name")}
          <input required value={name} onChange={(e) => setName(e.target.value)} className={field} autoComplete="name" placeholder={t("login.namePh")} />
        </label>
        <label className="text-sm font-medium text-ink-soft">
          {t("login.token")}
          <input required type="password" value={token} onChange={(e) => setToken(e.target.value)} className={field} autoComplete="current-password" />
        </label>
        {error && <p role="alert" className="rounded-md border border-red-line bg-red-tint px-3 py-2 text-red">{error}</p>}
        <button type="submit" disabled={busy} className="press inline-flex h-11 items-center justify-center gap-2 rounded-card bg-neel px-5 font-semibold text-on-neel transition-colors hover:bg-neel-hover disabled:opacity-60">
          <KeyRound aria-hidden size={18} />
          {busy ? t("login.checking") : t("login.open")}
        </button>
      </form>
      {health.data?.reviewer_login === "demo token" && (
        <p className="mt-6 rounded-md border border-dashed border-rule-strong px-3 py-2 text-sm text-ink-soft">
          {t.rich("login.demo", { code: (c) => <code className="font-mono text-ink">{c}</code> })}
        </p>
      )}
    </main>
  );
}

/* -------------------------------------------------------------- dashboard */

function Dashboard({ session, onSignOut }: { session: Session; onSignOut: () => void }) {
  const t = useTranslations("review");
  const queue = useApi<ReviewQueue>(() => api.queue(session.token), [session.token], 20000);
  const health = useApi(() => api.health(), []);
  const [sev, setSev] = useState<"all" | "red" | "amber">("all");
  const [route, setRoute] = useState<"all" | "doctor" | "pharmacist">("all");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  // below xl only some panels fit: phones show one, laptops show the queue plus one
  const [view, setView] = useState<"queue" | "evidence" | "patient">("queue");
  // findings to review, or family questions Sathi passed on
  const [mode, setMode] = useState<"flags" | "questions">("flags");
  const [openQuestions, setOpenQuestions] = useState<number>();
  useEffect(() => {
    api.reviewerQuestions(session.token).then((r) => setOpenQuestions(r.open)).catch(() => {});
  }, [session.token]);
  const [hidden, setHidden] = useState<Set<number>>(new Set());
  const [note, setNote] = useState("");
  const [noteError, setNoteError] = useState(false);
  const [toast, setToast] = useState<Toast | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const noteRef = useRef<HTMLTextAreaElement>(null);
  const rowRefs = useRef(new Map<number, HTMLButtonElement>());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30000);
    return () => clearInterval(id);
  }, []);

  const flags = useMemo(
    () =>
      (queue.data?.flags ?? []).filter(
        (f) => !hidden.has(f.id) && (sev === "all" || f.severity === sev) && (route === "all" || f.routed_to === route),
      ),
    [queue.data, hidden, sev, route],
  );
  const selected = flags.find((f) => f.id === selectedId) ?? flags[0] ?? null;
  const counts = queue.data?.counts;

  useEffect(() => {
    setNote("");
    setNoteError(false);
  }, [selected?.id]);

  const move = useCallback(
    (dir: 1 | -1) => {
      if (!flags.length) return;
      const i = Math.max(0, flags.findIndex((f) => f.id === selected?.id));
      const next = flags[Math.min(flags.length - 1, Math.max(0, i + dir))];
      setSelectedId(next.id);
      rowRefs.current.get(next.id)?.scrollIntoView({ block: "nearest" });
    },
    [flags, selected],
  );

  const decide = useCallback(
    async (status: "confirmed" | "dismissed") => {
      if (!selected) return;
      if (status === "dismissed" && !note.trim()) {
        setNoteError(true);
        noteRef.current?.focus();
        return;
      }
      const flag = selected;
      const i = flags.findIndex((f) => f.id === flag.id);
      const next = flags[i + 1] ?? flags[i - 1];
      setHidden((h) => new Set(h).add(flag.id)); // optimistic
      setSelectedId(next?.id ?? null);
      setToast({ flag, status, until: Date.now() + 5000 });
      try {
        await api.review(session.token, flag.id, { status, reviewer: session.name, note: note.trim() || undefined });
      } catch {
        setHidden((h) => { const n = new Set(h); n.delete(flag.id); return n; });
        setToast(null);
        setSelectedId(flag.id);
      }
    },
    [selected, flags, note, session],
  );

  const undo = useCallback(async () => {
    if (!toast) return;
    const { flag } = toast;
    setToast(null);
    await api.undo(session.token, flag.id, session.name);
    setHidden((h) => { const n = new Set(h); n.delete(flag.id); return n; });
    setSelectedId(flag.id);
    queue.reload();
  }, [toast, session, queue]);

  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => { setToast(null); queue.reload(); }, toast.until - Date.now());
    return () => clearTimeout(id);
  }, [toast, queue]);

  // Keyboard: J/K move, C confirm, D dismiss, N note, U undo. Off while typing.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (mode !== "flags") return;
      const typing = e.target instanceof HTMLElement && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName);
      if (typing) {
        if (e.key === "Escape") (e.target as HTMLElement).blur();
        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); decide("confirmed"); }
        return;
      }
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const k = e.key.toLowerCase();
      if (k === "j") { e.preventDefault(); move(1); }
      else if (k === "k") { e.preventDefault(); move(-1); }
      else if (k === "c") { e.preventDefault(); decide("confirmed"); }
      else if (k === "d") { e.preventDefault(); decide("dismissed"); }
      else if (k === "n") { e.preventDefault(); noteRef.current?.focus(); }
      else if (k === "u" && toast) { e.preventDefault(); undo(); }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [move, decide, undo, toast, mode]);

  return (
    // pinned to the window: header stays put, and queue, evidence and patient each scroll on their own
    <div className="flex h-dvh flex-col overflow-hidden">
      {/* the queue answers fast; /health can be slow, so either one is enough to show the bar */}
      {(health.data?.demo_mode || queue.data?.flags.some((f) => f.patient?.is_demo)) && <JudgeBar className="shrink-0" />}
      <header className="flex h-16 shrink-0 items-center gap-3 border-b border-rule bg-paper-raised px-4 sm:px-6 lg:gap-5">
        <Link href="/" title={t("backToSite")} className="shrink-0 rounded-md">
          <BrandMark size={30} className="sm:hidden" />
          <span className="sr-only sm:hidden">{t("home")}</span>
          <span className="hidden sm:inline-flex"><Wordmark /></span>
        </Link>
        <span className="hidden h-6 w-px bg-rule lg:block" aria-hidden />
        <h1 className="hidden whitespace-nowrap text-lg font-semibold text-ink lg:block">{t("dash.title")}</h1>
        <div role="group" aria-label={t("dash.mode")} className="inline-flex shrink-0 rounded-md border border-rule p-0.5">
          {([["flags", t("dash.findings")], ["questions", t("dash.questionsTab")]] as const).map(([key, label]) => (
            <button
              key={key}
              type="button"
              aria-pressed={mode === key}
              onClick={() => setMode(key)}
              className={cx("inline-flex h-9 items-center gap-1.5 whitespace-nowrap rounded px-2.5 text-sm font-medium sm:px-3",
                mode === key ? "bg-neel-tint text-ink" : "text-ink-soft hover:text-ink")}
            >
              {label}
              {key === "questions" && !!openQuestions && (
                <span className="tabular rounded-chip bg-neel px-1.5 text-[12px] font-semibold text-on-neel">{openQuestions}</span>
              )}
            </button>
          ))}
        </div>
        <dl className={cx("hidden items-center gap-4 text-sm", mode === "flags" && "md:flex")} aria-label={t("dash.counts")}>
          <Count label={t("dash.pending")} value={counts?.pending} />
          <Count label={t("dash.red")} value={counts?.red} tone="red" />
          <Count label={t("dash.amber")} value={counts?.amber} tone="amber" />
          <span aria-hidden className="hidden h-4 w-px bg-rule xl:block" />
          <Count label={t("dash.forDoctors")} value={counts?.doctor} className="hidden xl:flex" />
          <Count label={t("dash.forPharmacists")} value={counts?.pharmacist} className="hidden xl:flex" />
        </dl>
        <div className="ml-auto flex items-center gap-2 sm:gap-3">
          <span className="hidden max-w-[260px] truncate whitespace-nowrap text-sm text-ink-soft 2xl:inline">{t.rich("dash.signedIn", { name: session.name, b: (c) => <strong className="font-semibold text-ink">{c}</strong> })}</span>
          <Link href="/models?from=/review" title={t("dash.models")} aria-label={t("dash.models")} className="hidden h-10 sm:inline-flex min-w-10 items-center justify-center gap-1.5 whitespace-nowrap rounded-chip border border-rule px-2.5 text-sm font-medium text-ink-soft hover:text-ink">
            <Cpu aria-hidden size={16} /> <span className="hidden 2xl:inline">{t("dash.models")}</span>
          </Link>
          <ThemeToggle className="h-10 w-10" />
          <LangToggle className="h-10" />
          <button type="button" onClick={onSignOut} title={session.name} aria-label={t("dash.signOut")} className="inline-flex h-10 items-center gap-1.5 whitespace-nowrap rounded-chip border border-rule px-3 text-sm font-medium text-ink-soft hover:text-ink">
            <LogOut aria-hidden size={16} /> <span className="hidden lg:inline">{t("dash.signOut")}</span>
          </button>
        </div>
      </header>

      {mode === "questions" ? (
        <QuestionsBoard token={session.token} reviewer={session.name} now={now} onCount={setOpenQuestions} />
      ) : (<>
      <div role="tablist" aria-label={t("dash.panels")} className="flex shrink-0 gap-1 border-b border-rule bg-paper-raised px-3 py-2 lg:pl-[352px] xl:hidden">
        {([
          ["queue", `${t("dash.queue")}${counts ? ` (${counts.pending})` : ""}`, "lg:hidden"],
          ["evidence", t("dash.evidence"), ""],
          ["patient", t("dash.patient"), ""],
        ] as const).map(([key, text, extra]) => {
          const active = view === key;
          return (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => setView(key)}
              className={cx(
                "h-10 flex-1 rounded-md px-3 text-[15px] font-medium transition-colors",
                active ? "bg-neel-tint text-ink" : "text-ink-soft hover:text-ink",
                // laptops always show the queue, so "evidence" is the panel beside it by default
                key === "evidence" && view === "queue" && "lg:bg-neel-tint lg:text-ink",
                extra,
              )}
            >
              {text}
            </button>
          );
        })}
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 grid-rows-[minmax(0,1fr)] lg:grid-cols-[340px_minmax(0,1fr)] xl:grid-cols-[380px_minmax(0,1fr)_320px]">
        {/* queue */}
        <section aria-label={t("dash.queueLabel")} className={cx("min-h-0 flex-col border-rule lg:flex lg:border-r", view === "queue" ? "flex" : "hidden")}>
          <div className="grid gap-2 border-b border-rule px-4 py-3">
            <Segmented label={t("dash.severity")} value={sev} onChange={setSev} options={[["all", t("dash.all")], ["red", t("dash.red")], ["amber", t("dash.amber")]]} />
            <Segmented label={t("dash.route")} value={route} onChange={setRoute} options={[["all", t("dash.everyone")], ["doctor", t("dash.doctor")], ["pharmacist", t("dash.pharmacist")]]} />
          </div>
          <div role="listbox" aria-label={t("dash.queue")} className="relative min-h-0 flex-1 overflow-y-auto p-2">
            {queue.error ? (
              <p className="p-4 text-red">{t("dash.loadError")} {queue.error.message}</p>
            ) : !queue.data ? (
              <div className="grid gap-2 p-2">{[0, 1, 2, 3].map((i) => <div key={i} className="h-[68px] rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />)}</div>
            ) : flags.length === 0 ? (
              <div className="p-6 text-center">
                <CircleCheck aria-hidden size={36} className="mx-auto text-green" />
                <p className="mt-2 font-semibold text-ink">{t("dash.clearTitle")}</p>
                <p className="text-sm text-ink-soft">{t("dash.clearBody")}</p>
              </div>
            ) : (
              <div className="grid gap-1">
                {flags.map((f) => (
                  <ReviewRow
                    key={f.id}
                    ref={(el) => { if (el) rowRefs.current.set(f.id, el); }}
                    flag={f}
                    now={now}
                    selected={f.id === selected?.id}
                    onSelect={() => { setSelectedId(f.id); setView("evidence"); }}
                  />
                ))}
              </div>
            )}
          </div>
          <p className="hidden border-t border-rule px-4 py-2.5 text-[13px] text-ink-faint lg:block">
            <Kbd>J</Kbd>/<Kbd>K</Kbd> {t("dash.kMove")} · <Kbd>C</Kbd> {t("dash.kConfirm")} · <Kbd>D</Kbd> {t("dash.kDismiss")} · <Kbd>N</Kbd> {t("dash.kNote")}
          </p>
        </section>

        {/* evidence */}
        <section
          aria-label={t("dash.evidence")}
          className={cx(
            "relative min-h-0 overflow-y-auto px-4 py-5 sm:px-8 sm:py-6 xl:block",
            view === "evidence" ? "block" : "hidden",
            view === "patient" ? "lg:hidden" : "lg:block",
          )}
        >
          {selected ? (
            <Evidence key={selected.id} flag={selected} now={now} session={session}>
              <div className="mt-8 rounded-card border border-rule bg-paper-raised p-5">
                <label htmlFor="note" className="flex items-center gap-2 font-semibold text-ink">
                  <NotebookPen aria-hidden size={18} /> {t("dash.note")} <span className="font-normal text-ink-faint">{t("dash.noteHint")}</span>
                </label>
                <textarea
                  id="note"
                  ref={noteRef}
                  value={note}
                  onChange={(e) => { setNote(e.target.value); setNoteError(false); }}
                  rows={3}
                  aria-invalid={noteError}
                  aria-describedby={noteError ? "note-err" : undefined}
                  className={cx(
                    "mt-2 block w-full resize-y rounded-md border bg-paper px-3 py-2 text-base text-ink",
                    noteError ? "border-red" : "border-rule-strong",
                  )}
                  placeholder={t("dash.notePh")}
                />
                {noteError && <p id="note-err" className="mt-1.5 text-sm font-medium text-red">{t("dash.noteError")}</p>}
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  <button type="button" onClick={() => decide("confirmed")} className="press inline-flex h-11 items-center gap-2 rounded-card bg-neel px-5 font-semibold text-on-neel transition-colors hover:bg-neel-hover">
                    <Check aria-hidden size={18} strokeWidth={2.5} /> {t("dash.confirm")} <Kbd tone="onTeal">C</Kbd>
                  </button>
                  <button type="button" onClick={() => decide("dismissed")} className="press inline-flex h-11 items-center gap-2 rounded-card border border-rule-strong bg-paper-raised px-5 font-semibold text-ink hover:border-ink-faint">
                    <X aria-hidden size={18} strokeWidth={2.5} /> {t("dash.dismiss")} <Kbd>D</Kbd>
                  </button>
                  <span className="ml-auto hidden text-[13px] text-ink-faint lg:inline"><Kbd>Ctrl</Kbd>+<Kbd>Enter</Kbd> {t("dash.ctrlEnter")}</span>
                </div>
              </div>
            </Evidence>
          ) : (
            <div className="grid h-full place-items-center text-ink-faint">{t("dash.select")}</div>
          )}
        </section>

        {/* patient */}
        <aside
          aria-label={t("dash.patient")}
          tabIndex={0}
          className={cx(
            "relative min-h-0 overflow-y-auto border-rule bg-paper-raised/60 px-5 py-6 xl:block xl:border-l",
            view === "patient" ? "block" : "hidden",
          )}
        >
          {selected?.patient ? <PatientPanel session={session} patientId={selected.patient.id} key={selected.patient.id} /> : null}
        </aside>
      </div>
      </>)}

      {toast && (
        <div role="status" className="fixed bottom-6 left-1/2 z-20 flex w-max max-w-[calc(100vw-2rem)] -translate-x-1/2 flex-wrap items-center gap-x-4 gap-y-2 rounded-card border border-rule bg-ink px-5 py-3 text-paper shadow-soft" style={{ animation: "assemble 200ms var(--ease-out-quint) both" }}>
          <span>
            {toast.status === "confirmed" ? t("dash.toastConfirmed") : t("dash.toastDismissed")}: <strong>{toast.flag.items.map((i) => i.brand).join(" + ")}</strong>
          </span>
          <button type="button" onClick={undo} className="inline-flex h-9 items-center gap-1.5 rounded-chip border border-paper/40 px-3 text-sm font-semibold hover:bg-paper/10">
            <Undo2 aria-hidden size={16} /> {t("dash.undo")}
          </button>
          <UndoTimer until={toast.until} />
        </div>
      )}
    </div>
  );
}

function Evidence({ flag, now, session, children }: { flag: Flag; now: number; session: Session; children: React.ReactNode }) {
  const t = useTranslations("review");
  // the review-time clock starts when a reviewer first opens the finding
  useEffect(() => {
    api.opened(session.token, flag.id).catch(() => {});
  }, [session.token, flag.id]);
  const locale = useLocale();
  const ruleName = useRuleName();
  const generic = (flag.meta.generic as string | undefined) ?? flag.items[0]?.generic ?? "";
  const level = String(flag.meta.interaction_severity ?? "");
  const route = t(`routes.${flag.routed_to}`);
  const label =
    flag.code === "DUPLICATE_GENERIC"
      ? t(flag.items.length > 2 ? "ev.all" : "ev.both", { generic: genericName(generic, locale) })
      : flag.code === "INTERACTION"
        ? t("ev.interaction", { level: level === "major" || level === "moderate" ? t(`ev.${level}`) : level })
        : ruleName(flag.code);
  const web = flag.items.filter((i) => i.match_method === "web_unverified");
  return (
    <article style={{ animation: "assemble 200ms var(--ease-out-quint) both" }}>
      <header className="flex flex-wrap items-center gap-3">
        <SeverityBadge severity={flag.severity} label={t("ev.badge", { sev: flag.severity === "red" ? t("dash.red") : t("dash.amber"), route })} />
        <h2 className="font-display text-[26px] leading-[1.15] text-ink sm:text-[34px]">{ruleName(flag.code)}</h2>
      </header>
      <p className="mt-2 text-sm text-ink-soft">
        {flag.patient && <>{flag.patient.name}, {flag.patient.age} · </>}{t("ev.meta", { time: since(flag.created_at, now), route })}
        {flag.patient?.is_demo && <DemoTag className="ml-3 align-middle" />}
      </p>
      {flag.patient && <CaseSummaryPanel token={session.token} reviewer={session.name} patientId={flag.patient.id} />}

      <div className="mt-6">
        {flag.items.length >= 2 ? (
          <>
            {/* side by side needs room; phones stack the strips instead */}
            <div className="hidden sm:block">
              <DuplicateConnector orientation="horizontal" tone={flag.severity} label={label} delay={60}>
                {flag.items.map((it) => <StripCard key={it.id} item={it} density="compact" highlight={flag.severity} />)}
              </DuplicateConnector>
            </div>
            <div className="sm:hidden">
              <DuplicateConnector tone={flag.severity} label={label} delay={60}>
                {flag.items.map((it) => <StripCard key={it.id} item={it} density="compact" highlight={flag.severity} />)}
              </DuplicateConnector>
            </div>
          </>
        ) : (
          <div className="max-w-[440px]">
            {flag.items.map((it) => <StripCard key={it.id} item={it} density="compact" highlight={flag.severity} />)}
          </div>
        )}
      </div>

      <section className="mt-6 grid grid-cols-1 gap-x-6 gap-y-1 border-t border-rule pt-5 text-[15px] sm:grid-cols-[160px_minmax(0,1fr)] sm:gap-y-3 [&>h3:not(:first-child)]:mt-3 sm:[&>h3:not(:first-child)]:mt-0">
        <h3 className="font-semibold text-ink-soft">{t("ev.ruleFired")}</h3>
        <p lang="en" className="text-ink">{flag.evidence}{locale === "bn" && <span className="mt-1 block text-[13px] text-ink-faint">{t("ev.clinicalNote")}</span>}</p>
        <h3 className="font-semibold text-ink-soft">{t("ev.dataSource")}</h3>
        <p className="text-ink">{flag.data_source}</p>
        {web.length > 0 && (
          <>
            <h3 className="font-semibold text-amber">{t("ev.webMatch")}</h3>
            <ul className="grid gap-1">
              {web.map((i) => (
                <li key={i.id} className="text-ink">
                  {i.brand} → {i.generic} <span className="font-semibold text-amber">{t("ev.unverified")}</span>{" "}
                  {i.match_source && (
                    <a href={i.match_source} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 underline">
                      {i.match_source} <ExternalLink aria-hidden size={13} />
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </>
        )}
        <h3 className="font-semibold text-ink-soft">{t("ev.brandMatching")}</h3>
        <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={t("ev.brandMatching")}>
        <table className="w-full min-w-[480px] text-left text-[13px]">
          <thead className="text-ink-faint">
            <tr><th className="py-1 font-medium">{t("ev.thBrand")}</th><th className="font-medium">{t("ev.thGeneric")}</th><th className="font-medium">{t("ev.thMatch")}</th><th className="font-medium">{t("ev.thReadBy")}</th></tr>
          </thead>
          <tbody className="tabular text-ink-soft">
            {flag.items.map((i) => (
              <tr key={i.id} className="border-t border-rule">
                <td className="py-1.5 font-semibold text-ink">{i.brand} {i.strength}</td>
                <td>{i.generic ?? "—"} · {i.drug_class ?? "—"}</td>
                <td>{i.match_method}{i.match_score != null ? ` ${i.match_score}` : ""} <span className="text-ink-faint">({i.match_source ?? "—"})</span></td>
                <td>{i.model_id ?? "—"}{i.prompt_version ? ` · ${i.prompt_version}` : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </section>
      {children}
    </article>
  );
}

function PatientPanel({ session, patientId }: { session: Session; patientId: number }) {
  const token = session.token;
  const patient = useApi(() => api.patient(patientId, token), [patientId]);
  const items = useApi(() => api.items(patientId, token), [patientId]);
  const audit = useApi<AuditEntry[]>(() => api.audit(token, patientId), [patientId], 15000);
  const t = useTranslations("review");
  const tc = useTranslations("passport.conditions");
  const locale = useLocale();
  const ruleName = useRuleName();
  const p = patient.data;
  const confirmed = (items.data ?? []).filter((i) => i.confirmed);
  const prescribers = Array.from(new Set(confirmed.map((i) => i.prescriber).filter(Boolean))) as string[];
  if (!p) return <div className="h-40 rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />;
  return (
    <div className="grid gap-6">
      <section>
        <p lang="bn" className="font-bn-display text-[24px] leading-tight text-ink">{p.name_bn}</p>
        <p className="font-semibold text-ink">{p.name}</p>
        <p className="tabular text-sm text-ink-soft">{t("panel.years", { age: p.age })} · {p.district}</p>
        <p className="mt-1 text-sm text-ink-soft">{p.conditions.map((c) => (tc.has(c) ? tc(c) : c)).join(" · ")}</p>
      </section>
      <ClinicalEditor token={token} reviewer={session.name} patient={p} items={items.data ?? []}
        onChanged={() => { patient.reload(); items.reload(); }} />
      <section>
        <h3 className="flex items-center gap-1.5 text-[13px] font-semibold uppercase tracking-[0.06em] text-ink-faint"><Stethoscope aria-hidden size={14} /> {t("panel.prescribers")}</h3>
        <ul className="mt-2 grid gap-1 text-sm text-ink">{prescribers.map((x) => <li key={x}>{x}</li>)}</ul>
      </section>
      <section>
        <h3 className="flex items-center gap-1.5 text-[13px] font-semibold uppercase tracking-[0.06em] text-ink-faint"><History aria-hidden size={14} /> {t("panel.audit")}</h3>
        {audit.data?.length ? (
          <ol className="mt-2 grid gap-2.5 text-sm">
            {audit.data.slice(0, 12).map((a) => (
              <li key={a.id} className="border-l border-rule pl-3">
                <span className={cx("font-semibold", a.status === "confirmed" ? "text-neel" : a.status === "dismissed" ? "text-ink" : "text-ink-faint")}>{t(`panel.status.${a.status}`)}</span>{" "}
                <span className="text-ink-soft">{ruleName(a.code)}</span>
                <span className="block text-[13px] text-ink-faint">{a.reviewer} · {date(a.created_at, locale, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span>
                {a.note && <span className="mt-0.5 flex gap-1 text-[13px] text-ink-soft"><FileText aria-hidden size={12} className="mt-1 shrink-0" />{a.note}</span>}
              </li>
            ))}
          </ol>
        ) : (
          <p className="mt-2 text-sm text-ink-faint">{t("panel.noDecisions")}</p>
        )}
      </section>
    </div>
  );
}

function Segmented<T extends string>({ label, value, onChange, options }: {
  label: string; value: T; onChange: (v: T) => void; options: [T, string][];
}) {
  return (
    <div role="radiogroup" aria-label={label} className="grid grid-flow-col gap-1 rounded-card bg-paper-sunk p-1">
      {options.map(([v, text]) => (
        <button
          key={v}
          type="button"
          role="radio"
          aria-checked={value === v}
          onClick={() => onChange(v)}
          className={cx(
            "h-8 rounded-md px-2 text-sm font-medium transition-colors",
            value === v ? "bg-paper-raised text-ink shadow-soft" : "text-ink-soft hover:text-ink",
          )}
        >
          {text}
        </button>
      ))}
    </div>
  );
}

function Count({ label, value, tone, className = "flex" }: { label: string; value?: number; tone?: "red" | "amber"; className?: string }) {
  return (
    <div className={cx("items-baseline gap-1.5", className)}>
      <dt className="whitespace-nowrap text-ink-soft">{label}</dt>
      <dd className={cx("tabular text-lg font-semibold", tone === "red" ? "text-red" : tone === "amber" ? "text-amber" : "text-ink")}>
        {value ?? "–"}
      </dd>
    </div>
  );
}

function Kbd({ children, tone }: { children: React.ReactNode; tone?: "onTeal" }) {
  return (
    <kbd className={cx(
      "inline-flex h-5 min-w-5 items-center justify-center rounded border px-1 font-sans text-[12px] font-semibold leading-none",
      tone === "onTeal" ? "border-on-neel/40 text-on-neel" : "border-rule-strong bg-paper-raised text-ink-soft",
    )}>
      {children}
    </kbd>
  );
}

function UndoTimer({ until }: { until: number }) {
  const [left, setLeft] = useState(Math.ceil((until - Date.now()) / 1000));
  useEffect(() => {
    const id = setInterval(() => setLeft(Math.max(0, Math.ceil((until - Date.now()) / 1000))), 250);
    return () => clearInterval(id);
  }, [until]);
  return <span className="tabular w-6 text-right text-sm opacity-70">{left}s</span>;
}
