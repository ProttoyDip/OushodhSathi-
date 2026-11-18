"use client";

import { MessageCircle, Send } from "lucide-react";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useState } from "react";
import { buttonStyles } from "@/components/Chrome";
import { api, ApiError } from "@/lib/api";
import { cx } from "@/lib/format";
import type { WaCheckin } from "@/lib/types";

const OPEN = ["sent", "answering"];

/** The daily WhatsApp check-in in the browser: the same fixed messages and buttons as the real one.
 * Simulator only: nothing is sent to WhatsApp and no number is used. */
export function WhatsAppSimulator({ pid }: { pid: number }) {
  const t = useTranslations("calls.wa");
  const [c, setC] = useState<WaCheckin | null>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (fn: () => Promise<WaCheckin | null>) => {
    setBusy(true); setError(null);
    try { setC(await fn()); } catch (e) { setError(e instanceof ApiError ? e.message : String(e)); } finally { setBusy(false); }
  }, []);

  useEffect(() => { run(() => api.whatsappCurrent(pid)); }, [pid, run]);

  // with real WhatsApp keys the message went to the family's phone: answer it there, not here
  const real = c?.provider === "whatsapp";
  const open = c && OPEN.includes(c.status) && !real;
  const lastOurs = c ? [...c.transcript].reverse().find((m) => m.from === "us") : undefined;

  return (
    <section className="mx-auto w-full max-w-[420px] overflow-hidden rounded-[24px] border border-rule-strong bg-paper-raised">
      <header className="flex items-center gap-2 border-b border-rule px-4 py-3">
        <MessageCircle aria-hidden size={20} className="text-green" />
        <p className="font-semibold text-ink">{t("chatTitle")}</p>
      </header>
      <p className="px-4 pt-3 text-center text-[13px] text-ink-faint">{real ? t("sentToPhone") : t("simNote")}</p>

      <ol aria-live="polite" className="grid gap-2 px-3 py-3">
        {(c?.transcript ?? []).map((m, i) => (
          <li key={m.id ?? i} className={cx("max-w-[85%] rounded-2xl px-3.5 py-2 text-[17px] leading-snug",
            m.from === "us" ? "justify-self-start rounded-tl-sm bg-paper text-ink shadow-soft" : "justify-self-end rounded-tr-sm bg-green-tint text-ink")}>
            <span lang="bn">{m.from === "them" && m.text === "…" ? t("typed") : m.text}</span>
          </li>
        ))}
      </ol>

      {open && lastOurs && lastOurs.buttons.length > 0 && (
        <div className="grid gap-2 px-3 pb-3" role="group" aria-label={t("buttons")}>
          {lastOurs.buttons.map(([id, title]) => (
            <button key={id} type="button" disabled={busy} onClick={() => run(() => api.whatsappReply(c!.id, id, pid))}
              className="press min-h-12 rounded-card border border-rule-strong bg-paper text-[17px] font-semibold text-neel hover:border-neel">
              <span lang="bn">{title}</span>
            </button>
          ))}
        </div>
      )}

      {open ? (
        <form className="flex gap-2 border-t border-rule p-3" onSubmit={(e) => {
          e.preventDefault();
          if (text.trim()) { const v = text.trim(); setText(""); run(() => api.whatsappText(c!.id, v, pid)); }
        }}>
          <input value={text} onChange={(e) => setText(e.target.value)} maxLength={500} placeholder={t("typeHint")} aria-label={t("typeHint")}
            className="h-12 min-w-0 flex-1 rounded-chip border border-rule-strong bg-paper px-4 text-[16px] text-ink" />
          <button type="submit" disabled={busy || !text.trim()} aria-label={t("send")}
            className="press grid h-12 w-12 shrink-0 place-items-center rounded-full bg-neel text-on-neel"><Send aria-hidden size={18} /></button>
        </form>
      ) : (
        <div className="grid gap-2 border-t border-rule p-3 text-center">
          {c && <p className="text-ink-soft">{c.status === "emergency" ? t("endedEmergency") : c.status === "completed" ? t("ended") : t("none")}</p>}
          <button type="button" onClick={() => run(() => api.whatsappTest(pid))} disabled={busy} className={buttonStyles.primary}>
            <MessageCircle aria-hidden size={18} /> {t("sendNow")}
          </button>
        </div>
      )}
      {error && <p role="alert" className="px-4 pb-3 text-red">{error}</p>}
    </section>
  );
}
