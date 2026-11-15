"use client";

import { Phone, PhoneOff, Volume2 } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";
import { buttonStyles } from "@/components/Chrome";
import { api, ApiError } from "@/lib/api";
import { cx } from "@/lib/format";
import type { CallAttempt, CallTurn } from "@/lib/types";

const TIMEOUT_MS = 10_000; // like a real call: no key in 10 seconds counts as no answer to that question

/** The daily check-in call in the browser: the same prompts and keys (1 / 2 / 9) as the phone call.
 * Audio files are played when they exist in /audio/call/; the words are always on screen too. */
export function CallSimulator({ pid }: { pid: number }) {
  const t = useTranslations("calls.sim");
  const locale = useLocale() as "bn" | "en";
  const [ringing, setRinging] = useState<CallAttempt | null>(null);
  const [turn, setTurn] = useState<CallTurn | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [noAudio, setNoAudio] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async () => {
    try {
      const c = await api.currentCall(pid);
      if (c?.status === "ringing") setRinging(c);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  }, [pid]);

  useEffect(() => { load(); }, [load]);

  // play the prompts in order; a missing file is skipped and the words stay on screen
  useEffect(() => {
    if (!turn) return;
    let cancelled = false;
    (async () => {
      for (const id of turn.play) {
        if (cancelled) return;
        await new Promise<void>((done) => {
          const a = new Audio(`/audio/call/${id}.mp3`);
          a.onended = () => done();
          a.onerror = () => { setNoAudio(true); done(); };
          a.play().catch(() => { setNoAudio(true); done(); });
        });
      }
    })();
    return () => { cancelled = true; };
  }, [turn]);

  const press = useCallback(async (digit: "1" | "2" | "9" | null) => {
    if (!turn || turn.done) return;
    if (timer.current) clearTimeout(timer.current);
    setBusy(true);
    try {
      setTurn(await api.pressCall(pid, turn.attempt_id, digit, turn.seq));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [pid, turn]);

  // no key before the timeout: the call repeats the question once, then moves on
  useEffect(() => {
    if (!turn?.expects_input || turn.done) return;
    timer.current = setTimeout(() => press(null), TIMEOUT_MS);
    return () => { if (timer.current) clearTimeout(timer.current); };
  }, [turn, press]);

  async function ring() {
    setError(null); setTurn(null); setBusy(true);
    try {
      setRinging(await api.testCall(pid));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function answer() {
    if (!ringing) return;
    setBusy(true);
    try {
      setTurn(await api.answerCall(pid, ringing.id));
      setRinging(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function decline() {
    if (!ringing) return;
    await api.declineCall(pid, ringing.id).catch(() => undefined);
    setRinging(null);
  }

  const slotName = (s: string) => t(`slot.${s}`);

  return (
    <section aria-live="polite" className="mx-auto w-full max-w-[380px] rounded-[28px] border border-rule-strong bg-paper-raised p-5 shadow-sm">
      <p className="text-center text-sm text-ink-faint">{t("simNote")}</p>

      {!ringing && !turn && (
        <div className="mt-6 grid gap-3 text-center">
          <p className="text-ink-soft">{t("idle")}</p>
          <button type="button" onClick={ring} disabled={busy} className={buttonStyles.primary}>
            <Phone aria-hidden size={18} /> {t("ring")}
          </button>
        </div>
      )}

      {ringing && (
        <div className="mt-6 grid gap-5 text-center">
          <p className="font-bn-display text-2xl text-ink" style={{ animation: "breathe 1.6s ease-in-out infinite" }}>{t("incoming")}</p>
          <div className="grid grid-cols-2 gap-3">
            <button type="button" onClick={decline} className="press inline-flex min-h-14 items-center justify-center gap-2 rounded-full bg-red px-4 font-semibold text-white">
              <PhoneOff aria-hidden size={20} /> {t("decline")}
            </button>
            <button type="button" onClick={answer} disabled={busy} className="press inline-flex min-h-14 items-center justify-center gap-2 rounded-full bg-green px-4 font-semibold text-white">
              <Phone aria-hidden size={20} /> {t("answer")}
            </button>
          </div>
        </div>
      )}

      {turn && (
        <div className="mt-5 grid gap-4">
          <div className="grid gap-2 rounded-card bg-paper p-4">
            {turn.play.map((id) => (
              <p key={id} lang={locale} className={cx("flex gap-2 text-lg leading-relaxed text-ink", id === "emergency" && "font-semibold text-red")}>
                <Volume2 aria-hidden size={18} className="mt-1.5 shrink-0 text-neel" /> {turn.prompts[id][locale]}
              </p>
            ))}
          </div>
          {!turn.done ? (
            <div className="grid grid-cols-3 gap-3" role="group" aria-label={t("keypad")}>
              {(["1", "2", "9"] as const).map((d) => (
                <button key={d} type="button" disabled={busy} onClick={() => press(d)}
                  className={cx("press min-h-16 rounded-card border text-2xl font-semibold",
                    d === "9" ? "border-red-line text-red" : "border-rule-strong text-ink hover:bg-paper-sunk")}>
                  {locale === "bn" ? "০১২৩৪৫৬৭৮৯"[Number(d)] : d}
                </button>
              ))}
            </div>
          ) : (
            <div className="grid gap-2 border-t border-rule pt-3 text-ink-soft">
              <p className="font-semibold text-ink">{turn.status === "emergency" ? t("endedEmergency") : t("ended")}</p>
              {Object.entries(turn.answers).map(([slot, v]) => (
                <p key={slot}>{slotName(slot)}: {t(v === "taken" ? "taken" : "missed")}</p>
              ))}
              <button type="button" onClick={() => { setTurn(null); load(); }} className={buttonStyles.secondary}>{t("again")}</button>
            </div>
          )}
          {noAudio && <p className="text-[13px] text-ink-faint">{t("noAudio")}</p>}
        </div>
      )}

      {error && <p role="alert" className="mt-4 text-red">{error}</p>}
    </section>
  );
}
