"use client";

import { BookOpen, Check, Loader2, Mic, Phone, Send, ShieldQuestion, Volume2, X } from "lucide-react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { cx } from "@/lib/format";
import type { SathiReply, StepCode } from "@/lib/types";
import { SathiMark } from "./SathiMark";
import { useSpeechInput, useVoice } from "./speech";

type Message = { id: number; role: "user"; text: string } | { id: number; role: "sathi"; reply: SathiReply } | { id: number; role: "error" };

// quick replies follow where the family is in the flow
const CHIPS: Record<string, StepCode[]> = {
  scan: ["NO_SCAN"],
  confirm: ["ITEMS_TO_CONFIRM", "LOW_CONFIDENCE", "READY_TO_SEND"],
  review: ["SENT_FOR_REVIEW"],
  results: ["RESULTS_READY", "PASSPORT_NOT_SAVED", "REFILL_DUE", "ALL_GOOD", "PHARMACIST_REPLIED", "EMERGENCY_ACTIVE"],
};
const chipSet = (code?: StepCode) => Object.entries(CHIPS).find(([, codes]) => code && codes.includes(code))?.[0] ?? "scan";

/** Sathi: a floating button that opens the helper. Only on a household's pages. */
export function Sathi() {
  const { id } = useParams<{ id?: string }>();
  const pid = Number(id);
  if (!id || !Number.isFinite(pid)) return null;
  return <SathiHelper pid={pid} />;
}

function SathiHelper({ pid }: { pid: number }) {
  const t = useTranslations("sathi");
  const locale = useLocale();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [code, setCode] = useState<StepCode>();
  const fabRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const nextId = useRef(1);
  const speech = useSpeechInput(locale === "bn" ? "bn-BD" : "en-US", (text) => setInput((v) => (v ? `${v} ${text}` : text)));

  // the sheet is about the screen you are on; close it when you move
  useEffect(() => { setOpen(false); }, [pathname]);

  useEffect(() => {
    if (!open) return;
    api.nextStep(pid, locale).then((s) => setCode(s.code)).catch(() => {});
    inputRef.current?.focus();
    const fab = fabRef.current;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prevOverflow;
      fab?.focus(); // focus returns to the button that opened the sheet
    };
  }, [open, pid, locale]);

  // braces matter: newer browsers return a Promise from scrollIntoView, and an effect may only return a cleanup
  useEffect(() => { endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" }); }, [messages, busy]);

  const send = useCallback(async (question: string) => {
    const q = question.trim();
    if (!q || busy) return;
    setInput("");
    setMessages((m) => [...m, { id: nextId.current++, role: "user", text: q }]);
    setBusy(true);
    try {
      const reply = await api.askSathi(pid, q, locale);
      setMessages((m) => [...m, { id: nextId.current++, role: "sathi", reply }]);
    } catch {
      setMessages((m) => [...m, { id: nextId.current++, role: "error" }]);
    } finally {
      setBusy(false);
    }
  }, [busy, pid, locale]);

  // keep Tab inside the sheet; Escape closes it
  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") { e.preventDefault(); setOpen(false); return; }
    if (e.key !== "Tab" || !dialogRef.current) return;
    const items = dialogRef.current.querySelectorAll<HTMLElement>("a[href], button:not([disabled]), textarea, input, [tabindex='0']");
    if (!items.length) return;
    const first = items[0], last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  const chips = t.raw(`chips.${chipSet(code)}`) as string[];

  return (
    <>
      {/* stays mounted while the sheet is open, so focus can return to it on close */}
      <button
        ref={fabRef}
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={t("open")}
        className={cx("no-print press fixed right-4 z-30 h-14 w-14 items-center justify-center rounded-full shadow-soft ring-4 ring-paper", open ? "hidden" : "flex")}
        style={{ bottom: "calc(var(--sathi-offset, 20px) + env(safe-area-inset-bottom))" }}
      >
        <SathiMark size={56} />
      </button>

      {open && (
        <div className="no-print fixed inset-0 z-40 flex items-end justify-end sm:p-4" onKeyDown={onKeyDown}>
          <button type="button" aria-hidden tabIndex={-1} className="absolute inset-0 cursor-default bg-ink/40" onClick={() => setOpen(false)} />
          <div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="sathi-title"
            className="relative flex h-dvh w-full flex-col bg-paper text-[18px] sm:h-[min(680px,calc(100dvh-2rem))] sm:w-[440px] sm:rounded-card sm:border sm:border-rule sm:shadow-soft"
            style={{ animation: "assemble 220ms var(--ease-out-quint) both" }}
          >
            <header className="flex shrink-0 items-center gap-3 border-b border-rule px-4 py-3">
              <SathiMark size={36} />
              <div className="min-w-0 flex-1">
                <h2 id="sathi-title" className="font-bn-display text-[22px] leading-tight text-ink">{t("name")}</h2>
                <p className="text-[14px] text-ink-soft">{t("role")}</p>
              </div>
              <button type="button" onClick={() => setOpen(false)} aria-label={t("close")} className="press inline-flex h-12 w-12 items-center justify-center rounded-full border border-rule text-ink-soft hover:text-ink">
                <X aria-hidden size={22} />
              </button>
            </header>

            <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4" aria-live="polite">
              <div className="rounded-card border border-rule bg-paper-raised p-4">
                <p className="text-ink">{t("greeting")}</p>
              </div>
              <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label={t("suggestions")}>
                {chips.map((c) => (
                  <button key={c} type="button" disabled={busy} onClick={() => send(c)} className="press min-h-12 rounded-chip border border-neel/50 bg-neel-tint px-4 py-2 text-left text-base font-medium text-ink hover:border-neel disabled:opacity-60">
                    {c}
                  </button>
                ))}
              </div>

              <ol className="mt-5 grid gap-3">
                {messages.map((m) => (
                  <li key={m.id}>
                    {m.role === "user" ? (
                      <p className="ml-auto w-fit max-w-[85%] rounded-card bg-neel px-4 py-2.5 text-on-neel">{m.text}</p>
                    ) : m.role === "error" ? (
                      <p role="alert" className="w-fit max-w-[90%] rounded-card border border-rule bg-paper-raised px-4 py-3 text-ink-soft">{t("error")}</p>
                    ) : (
                      <ReplyCard reply={m.reply} pid={pid} />
                    )}
                  </li>
                ))}
                {busy && (
                  <li className="flex items-center gap-2 text-base text-ink-soft">
                    <Loader2 aria-hidden size={18} className="animate-spin motion-reduce:animate-none" /> {t("thinking")}
                  </li>
                )}
              </ol>
              <div ref={endRef} />
            </div>

            <form
              className="shrink-0 border-t border-rule bg-paper-raised px-3 pt-3 pb-[max(12px,env(safe-area-inset-bottom))]"
              onSubmit={(e) => { e.preventDefault(); send(input); }}
            >
              {speech.note && <p className="mb-2 px-1 text-[15px] text-ink-soft" role="status">{t(speech.note)}</p>}
              <div className="flex items-end gap-2">
                <label htmlFor="sathi-input" className="sr-only">{t("inputLabel")}</label>
                <textarea
                  id="sathi-input"
                  ref={inputRef}
                  rows={1}
                  value={input}
                  maxLength={500}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); } }}
                  placeholder={t("placeholder")}
                  className="block max-h-32 min-h-12 flex-1 resize-none rounded-card border border-rule-strong bg-paper px-3 py-2.5 text-[18px] text-ink"
                />
                <button
                  type="button"
                  onClick={speech.toggle}
                  aria-pressed={speech.listening}
                  aria-label={speech.listening ? t("micStop") : t("mic")}
                  className={cx(
                    "press inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full border",
                    speech.listening ? "border-red bg-red-tint text-red motion-safe:animate-pulse" : "border-rule-strong text-ink-soft hover:text-ink",
                  )}
                >
                  <Mic aria-hidden size={22} />
                </button>
                <button type="submit" disabled={!input.trim() || busy} aria-label={t("send")} className="press inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-neel text-on-neel disabled:opacity-50">
                  <Send aria-hidden size={20} />
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

function ReplyCard({ reply, pid }: { reply: SathiReply; pid: number }) {
  const t = useTranslations("sathi");
  if (reply.kind === "emergency") {
    const call = reply.actions.find((a) => a.tel);
    return (
      <div role="alert" className="rounded-card border-2 border-red bg-red-tint p-4">
        <p className="font-semibold text-red">{reply.text}</p>
        {call && (
          <a href={`tel:${call.tel}`} className="press mt-3 inline-flex min-h-14 w-full items-center justify-center gap-2.5 rounded-card bg-red px-6 text-lg font-semibold text-paper">
            <Phone aria-hidden size={22} /> {call.label}
          </a>
        )}
      </div>
    );
  }
  if (reply.kind === "medical_redirect") {
    return <MedicalRedirect reply={reply} pid={pid} />;
  }
  const action = reply.actions.find((a) => a.route);
  return (
    <div className="max-w-[92%] rounded-card border border-rule bg-paper-raised p-4">
      {reply.kind === "answer" && (
        <p className="mb-1.5 flex items-center gap-1.5 text-[14px] font-medium text-ink-soft">
          <BookOpen aria-hidden size={15} /> {t("fromGuide")}
        </p>
      )}
      <p className="text-ink">{reply.text}</p>
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1">
        {action?.route && (
          <Link href={action.route} className="inline-flex min-h-11 items-center font-semibold text-neel underline underline-offset-4">
            {action.label}
          </Link>
        )}
        <ListenButton text={reply.text} />
      </div>
    </div>
  );
}

function MedicalRedirect({ reply, pid }: { reply: SathiReply; pid: number }) {
  const t = useTranslations("sathi");
  const action = reply.actions[0];
  const [draft, setDraft] = useState(action?.question_draft ?? "");
  const [state, setState] = useState<"idle" | "sending" | "sent" | "failed">("idle");
  return (
    <div className="max-w-[92%] rounded-card border border-amber-line bg-amber-tint/60 p-4">
      <p className="flex items-start gap-2 text-ink">
        <ShieldQuestion aria-hidden size={20} className="mt-1 shrink-0 text-amber" />
        <span>{reply.text}</span>
      </p>
      <ListenButton text={reply.text} />
      {state === "sent" ? (
        <p className="mt-3 flex items-start gap-2 font-medium text-ink" role="status">
          <Check aria-hidden size={20} className="mt-1 shrink-0 text-green" />
          <span>{t("sent")} <Link href={`/p/${pid}/questions`} className="text-neel underline underline-offset-4">{t("seeQuestions")}</Link></span>
        </p>
      ) : (
        <form
          className="mt-3 grid gap-2"
          onSubmit={async (e) => {
            e.preventDefault();
            if (draft.trim().length < 2) return;
            setState("sending");
            try {
              await api.askPharmacist(pid, draft.trim());
              setState("sent");
            } catch {
              setState("failed");
            }
          }}
        >
          <label className="text-[15px] text-ink-soft">
            {t("draftLabel")}
            <textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={2} maxLength={1000} className="mt-1 block w-full resize-y rounded-md border border-rule-strong bg-paper px-3 py-2 text-[17px] text-ink" />
          </label>
          {state === "failed" && <p role="alert" className="text-[15px] text-red">{t("error")}</p>}
          <button type="submit" disabled={state === "sending" || draft.trim().length < 2} className="press inline-flex min-h-12 items-center justify-center gap-2 rounded-card bg-neel px-5 font-semibold text-on-neel disabled:opacity-60">
            <Send aria-hidden size={18} /> {action?.label ?? t("askPharmacist")}
          </button>
        </form>
      )}
    </div>
  );
}

/** "Listen": reads the answer aloud with a Bangla voice; hidden when the phone has none. */
export function ListenButton({ text, className }: { text: string; className?: string }) {
  const t = useTranslations("sathi");
  const locale = useLocale();
  const voice = useVoice(locale === "bn" ? "bn" : "en");
  const [speaking, setSpeaking] = useState(false);
  if (!voice) return null;
  return (
    <button
      type="button"
      onClick={() => {
        const synth = window.speechSynthesis;
        if (speaking) { synth.cancel(); setSpeaking(false); return; }
        const u = new SpeechSynthesisUtterance(text);
        u.voice = voice;
        u.lang = voice.lang;
        u.rate = 0.9;
        u.onend = u.onerror = () => setSpeaking(false);
        synth.cancel();
        synth.speak(u);
        setSpeaking(true);
      }}
      aria-pressed={speaking}
      className={cx("inline-flex min-h-11 items-center gap-1.5 font-medium text-ink-soft hover:text-ink", className)}
    >
      <Volume2 aria-hidden size={18} /> {speaking ? t("stopListening") : t("listen")}
    </button>
  );
}
