"use client";

import { Check, Clock, MessageSquareReply } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { api } from "@/lib/api";
import { cx, date, since } from "@/lib/format";
import type { Question } from "@/lib/types";
import { useApi } from "@/lib/useApi";

const DAY = 24 * 60 * 60 * 1000;

/** Family questions Sathi passed on. A pharmacist or doctor writes every reply; target 1–2 days. */
export function QuestionsBoard({ token, reviewer, now, onCount }: {
  token: string;
  reviewer: string;
  now: number;
  onCount?: (n: number) => void;
}) {
  const t = useTranslations("review.questions");
  const [status, setStatus] = useState<"open" | "all">("open");
  const qs = useApi(async () => {
    const r = await api.reviewerQuestions(token, status);
    onCount?.(r.open);
    return r;
  }, [token, status], 30000);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto max-w-[860px] px-4 py-6 sm:px-8">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-ink">{t("title")}</h2>
            <p className="mt-1 max-w-[62ch] text-sm text-ink-soft">{t("intro")}</p>
          </div>
          <div role="group" aria-label={t("filter")} className="inline-flex rounded-md border border-rule p-0.5">
            {(["open", "all"] as const).map((s) => (
              <button
                key={s}
                type="button"
                aria-pressed={status === s}
                onClick={() => setStatus(s)}
                className={cx("h-9 rounded px-3 text-sm font-medium", status === s ? "bg-neel-tint text-ink" : "text-ink-soft hover:text-ink")}
              >
                {t(s)}
              </button>
            ))}
          </div>
        </div>

        {qs.error ? (
          <p className="mt-6 text-red">{qs.error.message}</p>
        ) : !qs.data ? (
          <div className="mt-6 grid gap-3">{[0, 1].map((i) => <div key={i} className="h-36 rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />)}</div>
        ) : qs.data.questions.length === 0 ? (
          <p className="mt-8 text-center text-ink-soft">{status === "open" ? t("noneOpen") : t("none")}</p>
        ) : (
          <ol className="mt-6 grid gap-4">
            {qs.data.questions.map((q) => (
              <QuestionRow key={q.id} q={q} token={token} reviewer={reviewer} now={now} onReplied={qs.reload} />
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}

function QuestionRow({ q, token, reviewer, now, onReplied }: {
  q: Question; token: string; reviewer: string; now: number; onReplied: () => void;
}) {
  const t = useTranslations("review.questions");
  const locale = useLocale();
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const age = now - Date.parse(q.created_at);
  const tone = q.reply ? "done" : age > 2 * DAY ? "late" : age > DAY ? "due" : "ok";
  const p = q.patient;

  return (
    <li className={cx("rounded-card border bg-paper-raised p-5", tone === "late" ? "border-red-line" : tone === "due" ? "border-amber-line" : "border-rule")}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-ink-soft">
        {p && <span className="font-semibold text-ink">{locale === "bn" ? p.name_bn ?? p.name : p.name}, {p.age}</span>}
        {p?.is_demo && <span className="rounded-chip border border-dashed border-rule-strong px-2 text-[12px]">{t("demo")}</span>}
        <span className={cx("inline-flex items-center gap-1", tone === "late" ? "font-semibold text-red" : tone === "due" ? "font-semibold text-amber" : "")}>
          <Clock aria-hidden size={14} /> {t("waiting", { time: since(q.created_at, now) })}
          {tone === "late" && ` · ${t("overdue")}`}
        </span>
      </div>
      <p className="mt-2 whitespace-pre-wrap break-words text-base text-ink">{q.text}</p>

      {q.reply ? (
        <div className="mt-4 rounded-md border-l-4 border-neel bg-neel-tint/50 p-3">
          <p className="flex items-center gap-1.5 text-sm font-semibold text-neel"><Check aria-hidden size={16} /> {t("repliedBy", { name: q.replied_by ?? "", date: date(q.replied_at, locale) })}</p>
          <p className="mt-1 whitespace-pre-wrap text-ink">{q.reply}</p>
        </div>
      ) : (
        <form
          className="mt-4 grid gap-2"
          onSubmit={async (e) => {
            e.preventDefault();
            if (reply.trim().length < 2) return;
            setBusy(true);
            setError(false);
            try {
              await api.reply(token, q.id, reply.trim(), reviewer);
              onReplied();
            } catch {
              setError(true);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label htmlFor={`reply-${q.id}`} className="text-sm font-semibold text-ink">{t("replyLabel")}</label>
          <textarea
            id={`reply-${q.id}`}
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            rows={3}
            maxLength={2000}
            placeholder={t("replyPh")}
            className="block w-full resize-y rounded-md border border-rule-strong bg-paper px-3 py-2 text-base text-ink"
          />
          {error && <p role="alert" className="text-sm font-medium text-red">{t("failed")}</p>}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-[13px] text-ink-faint">{t("humanOnly")}</p>
            <button type="submit" disabled={busy || reply.trim().length < 2} className="press inline-flex h-11 items-center gap-2 rounded-card bg-neel px-5 font-semibold text-on-neel transition-colors hover:bg-neel-hover disabled:opacity-60">
              <MessageSquareReply aria-hidden size={18} /> {t("send")}
            </button>
          </div>
        </form>
      )}
    </li>
  );
}
