"use client";

import {
  Check, CircleCheck, ExternalLink, FileText, History, KeyRound, LogOut, NotebookPen, Pill, Stethoscope, Undo2, X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Wordmark } from "@/components/BrandMark";
import { DemoTag, ThemeToggle } from "@/components/Chrome";
import { DuplicateConnector } from "@/components/DuplicateConnector";
import { RULE_NAME, ReviewRow } from "@/components/ReviewRow";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StripCard } from "@/components/StripCard";
import { api, ApiError } from "@/lib/api";
import { cx, date, genericName, since } from "@/lib/format";
import type { AuditEntry, Flag, MedicineItem, ReviewQueue } from "@/lib/types";
import { useApi } from "@/lib/useApi";

const SESSION = "oushodh:reviewer";

type Session = { token: string; name: string };
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
  const [name, setName] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);
  const field = "mt-1.5 block h-11 w-full rounded-md border border-rule-strong bg-paper px-3 text-base text-ink";

  return (
    <main className="mx-auto flex min-h-dvh max-w-[420px] flex-col justify-center px-6 py-12">
      <Wordmark />
      <h1 className="mt-8 font-display text-[40px] leading-[1.05] text-ink">Clinical review</h1>
      <p className="mt-2 text-ink-soft">
        Pharmacists and doctors confirm or dismiss every finding before a family sees it.
      </p>
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
            setError(err instanceof ApiError && err.status === 401 ? "That reviewer token is not right." : "Can't reach the review server.");
          } finally {
            setBusy(false);
          }
        }}
      >
        <label className="text-sm font-medium text-ink-soft">
          Your name (recorded with every decision)
          <input required value={name} onChange={(e) => setName(e.target.value)} className={field} autoComplete="name" placeholder="e.g. Pharm. S. Akter" />
        </label>
        <label className="text-sm font-medium text-ink-soft">
          Reviewer token
          <input required type="password" value={token} onChange={(e) => setToken(e.target.value)} className={field} autoComplete="current-password" />
        </label>
        {error && <p role="alert" className="rounded-md border border-red-line bg-red-tint px-3 py-2 text-red">{error}</p>}
        <button type="submit" disabled={busy} className="inline-flex h-11 items-center justify-center gap-2 rounded-card bg-neel px-5 font-semibold text-on-neel transition-colors hover:bg-neel-hover disabled:opacity-60">
          <KeyRound aria-hidden size={18} />
          {busy ? "Checking…" : "Open the queue"}
        </button>
      </form>
      {health.data?.reviewer_login === "demo token" && (
        <p className="mt-6 rounded-md border border-dashed border-rule-strong px-3 py-2 text-sm text-ink-soft">
          Demo server: the reviewer token is <code className="font-mono text-ink">demo-reviewer</code>. Set REVIEWER_TOKEN in backend/.env for real use.
        </p>
      )}
    </main>
  );
}

/* -------------------------------------------------------------- dashboard */

function Dashboard({ session, onSignOut }: { session: Session; onSignOut: () => void }) {
  const queue = useApi<ReviewQueue>(() => api.queue(session.token), [session.token], 20000);
  const [sev, setSev] = useState<"all" | "red" | "amber">("all");
  const [route, setRoute] = useState<"all" | "doctor" | "pharmacist">("all");
  const [selectedId, setSelectedId] = useState<number | null>(null);
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
  }, [move, decide, undo, toast]);

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="flex h-16 shrink-0 items-center gap-6 border-b border-rule bg-paper-raised px-6">
        <Wordmark />
        <span className="h-6 w-px bg-rule" aria-hidden />
        <h1 className="text-lg font-semibold text-ink">Review queue</h1>
        <dl className="flex items-center gap-5 text-sm" aria-label="Pending counts">
          <Count label="Pending" value={counts?.pending} />
          <Count label="Red" value={counts?.red} tone="red" />
          <Count label="Amber" value={counts?.amber} tone="amber" />
          <span aria-hidden className="h-4 w-px bg-rule" />
          <Count label="For doctors" value={counts?.doctor} />
          <Count label="For pharmacists" value={counts?.pharmacist} />
        </dl>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-sm text-ink-soft">Signed in as <strong className="font-semibold text-ink">{session.name}</strong></span>
          <ThemeToggle className="h-10 w-10" />
          <button type="button" onClick={onSignOut} className="inline-flex h-10 items-center gap-1.5 rounded-chip border border-rule px-3 text-sm font-medium text-ink-soft hover:text-ink">
            <LogOut aria-hidden size={16} /> Sign out
          </button>
        </div>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-[380px_minmax(0,1fr)_320px]">
        {/* queue */}
        <section aria-label="Findings waiting for review" className="flex min-h-0 flex-col border-r border-rule">
          <div className="grid gap-2 border-b border-rule px-4 py-3">
            <Segmented label="Severity" value={sev} onChange={setSev} options={[["all", "All"], ["red", "Red"], ["amber", "Amber"]]} />
            <Segmented label="Route" value={route} onChange={setRoute} options={[["all", "Everyone"], ["doctor", "Doctor"], ["pharmacist", "Pharmacist"]]} />
          </div>
          <div role="listbox" aria-label="Queue" className="min-h-0 flex-1 overflow-y-auto p-2">
            {queue.error ? (
              <p className="p-4 text-red">Could not load the queue. {queue.error.message}</p>
            ) : !queue.data ? (
              <div className="grid gap-2 p-2">{[0, 1, 2, 3].map((i) => <div key={i} className="h-[68px] rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />)}</div>
            ) : flags.length === 0 ? (
              <div className="p-6 text-center">
                <CircleCheck aria-hidden size={36} className="mx-auto text-green" />
                <p className="mt-2 font-semibold text-ink">Queue clear</p>
                <p className="text-sm text-ink-soft">No findings are waiting with these filters.</p>
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
                    onSelect={() => setSelectedId(f.id)}
                  />
                ))}
              </div>
            )}
          </div>
          <p className="border-t border-rule px-4 py-2.5 text-[13px] text-ink-faint">
            <Kbd>J</Kbd>/<Kbd>K</Kbd> move · <Kbd>C</Kbd> confirm · <Kbd>D</Kbd> dismiss · <Kbd>N</Kbd> note
          </p>
        </section>

        {/* evidence */}
        <section aria-label="Evidence" className="min-h-0 overflow-y-auto px-8 py-6">
          {selected ? (
            <Evidence key={selected.id} flag={selected} now={now}>
              <div className="mt-8 rounded-card border border-rule bg-paper-raised p-5">
                <label htmlFor="note" className="flex items-center gap-2 font-semibold text-ink">
                  <NotebookPen aria-hidden size={18} /> Note <span className="font-normal text-ink-faint">— shown to the family with a confirmed finding; required to dismiss</span>
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
                  placeholder="Plain words. Do not write doses or tell the family to stop or change a medicine."
                />
                {noteError && <p id="note-err" className="mt-1.5 text-sm font-medium text-red">Add a short note to dismiss this finding.</p>}
                <div className="mt-4 flex items-center gap-3">
                  <button type="button" onClick={() => decide("confirmed")} className="inline-flex h-11 items-center gap-2 rounded-card bg-neel px-5 font-semibold text-on-neel transition-colors hover:bg-neel-hover">
                    <Check aria-hidden size={18} strokeWidth={2.5} /> Confirm <Kbd tone="onTeal">C</Kbd>
                  </button>
                  <button type="button" onClick={() => decide("dismissed")} className="inline-flex h-11 items-center gap-2 rounded-card border border-rule-strong bg-paper-raised px-5 font-semibold text-ink hover:border-ink-faint">
                    <X aria-hidden size={18} strokeWidth={2.5} /> Dismiss <Kbd>D</Kbd>
                  </button>
                  <span className="ml-auto text-[13px] text-ink-faint"><Kbd>Ctrl</Kbd>+<Kbd>Enter</Kbd> confirms from the note</span>
                </div>
              </div>
            </Evidence>
          ) : (
            <div className="grid h-full place-items-center text-ink-faint">Select a finding.</div>
          )}
        </section>

        {/* patient */}
        <aside aria-label="Patient" className="min-h-0 overflow-y-auto border-l border-rule bg-paper-raised/60 px-5 py-6">
          {selected?.patient ? <PatientPanel token={session.token} patientId={selected.patient.id} key={selected.patient.id} /> : null}
        </aside>
      </div>

      {toast && (
        <div role="status" className="fixed bottom-6 left-1/2 z-20 flex -translate-x-1/2 items-center gap-4 rounded-card border border-rule bg-ink px-5 py-3 text-paper shadow-soft" style={{ animation: "assemble 200ms var(--ease-out-quint) both" }}>
          <span>
            {toast.status === "confirmed" ? "Confirmed" : "Dismissed"}: <strong>{toast.flag.items.map((i) => i.brand).join(" + ")}</strong>
          </span>
          <button type="button" onClick={undo} className="inline-flex h-9 items-center gap-1.5 rounded-chip border border-paper/40 px-3 text-sm font-semibold hover:bg-paper/10">
            <Undo2 aria-hidden size={16} /> Undo (U)
          </button>
          <UndoTimer until={toast.until} />
        </div>
      )}
    </div>
  );
}

function Evidence({ flag, now, children }: { flag: Flag; now: number; children: React.ReactNode }) {
  const generic = (flag.meta.generic as string | undefined) ?? flag.items[0]?.generic ?? "";
  const label =
    flag.code === "DUPLICATE_GENERIC"
      ? `${flag.items.length > 2 ? "All are" : "Both are"} ${genericName(generic, "en").toLowerCase()}`
      : flag.code === "INTERACTION"
        ? `${String(flag.meta.interaction_severity ?? "")} interaction`.trim()
        : RULE_NAME[flag.code];
  const web = flag.items.filter((i) => i.match_method === "web_unverified");
  return (
    <article style={{ animation: "assemble 200ms var(--ease-out-quint) both" }}>
      <header className="flex flex-wrap items-center gap-3">
        <SeverityBadge severity={flag.severity} label={`${flag.severity === "red" ? "Red" : "Amber"} · for the ${flag.routed_to}`} />
        <h2 className="font-display text-[34px] leading-none text-ink">{RULE_NAME[flag.code]}</h2>
      </header>
      <p className="mt-2 text-sm text-ink-soft">
        {flag.patient && <>{flag.patient.name}, {flag.patient.age} · </>}waiting {since(flag.created_at, now)} · routed to {flag.routed_to}
        {flag.patient?.is_demo && <DemoTag className="ml-3 align-middle" label="Demo household — invented data" />}
      </p>

      <div className="mt-6">
        {flag.items.length >= 2 ? (
          <DuplicateConnector orientation="horizontal" tone={flag.severity} label={label} delay={60}>
            {flag.items.map((it) => <StripCard key={it.id} item={it} density="compact" highlight={flag.severity} />)}
          </DuplicateConnector>
        ) : (
          <div className="max-w-[440px]">
            {flag.items.map((it) => <StripCard key={it.id} item={it} density="compact" highlight={flag.severity} />)}
          </div>
        )}
      </div>

      <section className="mt-6 grid grid-cols-[160px_1fr] gap-x-6 gap-y-3 border-t border-rule pt-5 text-[15px]">
        <h3 className="font-semibold text-ink-soft">Rule that fired</h3>
        <p className="text-ink">{flag.evidence}</p>
        <h3 className="font-semibold text-ink-soft">Data source</h3>
        <p className="text-ink">{flag.data_source}</p>
        {web.length > 0 && (
          <>
            <h3 className="font-semibold text-amber">Web match</h3>
            <ul className="grid gap-1">
              {web.map((i) => (
                <li key={i.id} className="text-ink">
                  {i.brand} → {i.generic} <span className="font-semibold text-amber">unverified</span>{" "}
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
        <h3 className="font-semibold text-ink-soft">Brand matching</h3>
        <table className="w-full text-left text-[13px]">
          <thead className="text-ink-faint">
            <tr><th className="py-1 font-medium">Brand</th><th className="font-medium">Generic · class</th><th className="font-medium">Match</th><th className="font-medium">Read by</th></tr>
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
      </section>
      {children}
    </article>
  );
}

function PatientPanel({ token, patientId }: { token: string; patientId: number }) {
  const patient = useApi(() => api.patient(patientId), [patientId]);
  const items = useApi(() => api.items(patientId), [patientId]);
  const audit = useApi<AuditEntry[]>(() => api.audit(token, patientId), [patientId], 15000);
  const p = patient.data;
  const confirmed = (items.data ?? []).filter((i) => i.confirmed);
  const prescribers = Array.from(new Set(confirmed.map((i) => i.prescriber).filter(Boolean))) as string[];
  if (!p) return <div className="h-40 rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />;
  return (
    <div className="grid gap-6">
      <section>
        <p lang="bn" className="font-bn-display text-[24px] leading-tight text-ink">{p.name_bn}</p>
        <p className="font-semibold text-ink">{p.name}</p>
        <p className="tabular text-sm text-ink-soft">{p.age} years · {p.district}</p>
        <p className="mt-1 text-sm text-ink-soft">{p.conditions.join(" · ")}</p>
      </section>
      <section>
        <h3 className="flex items-center gap-1.5 text-[13px] font-semibold uppercase tracking-[0.06em] text-ink-faint"><Pill aria-hidden size={14} /> Confirmed medicines ({confirmed.length})</h3>
        <ul className="mt-2 grid gap-1.5 text-sm">
          {confirmed.map((i: MedicineItem) => (
            <li key={i.id} className="flex items-baseline justify-between gap-2">
              <span className="font-medium text-ink">{i.brand} <span className="tabular font-normal text-ink-soft">{i.strength}</span></span>
              <span className="truncate text-ink-soft">{i.generic ?? "unknown"}</span>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h3 className="flex items-center gap-1.5 text-[13px] font-semibold uppercase tracking-[0.06em] text-ink-faint"><Stethoscope aria-hidden size={14} /> Prescribers</h3>
        <ul className="mt-2 grid gap-1 text-sm text-ink">{prescribers.map((x) => <li key={x}>{x}</li>)}</ul>
      </section>
      <section>
        <h3 className="flex items-center gap-1.5 text-[13px] font-semibold uppercase tracking-[0.06em] text-ink-faint"><History aria-hidden size={14} /> Decisions (audit trail)</h3>
        {audit.data?.length ? (
          <ol className="mt-2 grid gap-2.5 text-sm">
            {audit.data.slice(0, 12).map((a) => (
              <li key={a.id} className="border-l border-rule pl-3">
                <span className={cx("font-semibold", a.status === "confirmed" ? "text-neel" : a.status === "dismissed" ? "text-ink" : "text-ink-faint")}>{a.status}</span>{" "}
                <span className="text-ink-soft">{RULE_NAME[a.code]}</span>
                <span className="block text-[13px] text-ink-faint">{a.reviewer} · {date(a.created_at, "en", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span>
                {a.note && <span className="mt-0.5 flex gap-1 text-[13px] text-ink-soft"><FileText aria-hidden size={12} className="mt-1 shrink-0" />{a.note}</span>}
              </li>
            ))}
          </ol>
        ) : (
          <p className="mt-2 text-sm text-ink-faint">No decisions yet.</p>
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

function Count({ label, value, tone }: { label: string; value?: number; tone?: "red" | "amber" }) {
  return (
    <div className="flex items-baseline gap-1.5">
      <dt className="text-ink-soft">{label}</dt>
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
