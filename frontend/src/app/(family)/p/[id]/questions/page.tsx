"use client";

import { Clock, MessageSquareReply, Send, UserRound } from "lucide-react";
import { useParams, useSearchParams } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { Suspense, useEffect, useState } from "react";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { ErrorState, Skeleton } from "@/components/States";
import { ListenButton } from "@/components/sathi/Sathi";
import { api, ApiError } from "@/lib/api";
import { cx, date } from "@/lib/format";
import { reveal } from "@/lib/reveal";
import { useApi } from "@/lib/useApi";

export default function QuestionsPage() {
  return (
    <Suspense>
      <Questions />
    </Suspense>
  );
}

/** Questions to the pharmacist and their replies. Replies are written by a person, never by AI. */
function Questions() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const t = useTranslations("questions");
  const tc = useTranslations("common");
  const locale = useLocale();
  const patient = useApi(() => api.patient(pid), [pid]);
  const questions = useApi(() => api.questions(pid), [pid], 30000);
  const [text, setText] = useState(useSearchParams().get("draft") ?? "");
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string>();

  // opening this screen counts as reading the replies
  const replies = questions.data?.filter((q) => q.reply && !q.reply_seen_at).length ?? 0;
  useEffect(() => {
    if (replies) api.questionsSeen(pid).catch(() => {});
  }, [pid, replies]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (text.trim().length < 2) return;
    setState("sending");
    setError(undefined);
    try {
      const q = await api.askPharmacist(pid, text.trim());
      questions.setData([q, ...(questions.data ?? [])]);
      setText("");
      setState("sent");
    } catch (err) {
      setState("idle");
      setError(err instanceof ApiError && err.status === 429 ? tc("errorTooMany") : tc("errorGeneric"));
    }
  }

  return (
    <>
      <FamilyHeader back={`/p/${pid}`} demo={patient.data?.is_demo} />
      <main className={`mx-auto w-full px-4 pb-12 pt-4 lg:pt-8 ${familyWidth}`}>
        <h1 className="font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t("title")}</h1>
        <p className="mt-2 max-w-[62ch] text-ink-soft">{t("intro")}</p>

        <div className="mt-6 grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:items-start lg:gap-x-10">
          <form {...reveal(0)} onSubmit={submit} className="grid gap-3 rounded-card border border-rule bg-paper-raised p-5">
            <label htmlFor="question" className="font-semibold text-ink">{t("askLabel")}</label>
            <textarea
              id="question"
              value={text}
              onChange={(e) => { setText(e.target.value); setState("idle"); }}
              rows={4}
              maxLength={1000}
              placeholder={t("placeholder")}
              className="block w-full resize-y rounded-md border border-rule-strong bg-paper px-3 py-2.5 text-lg text-ink"
            />
            <p className="text-[15px] text-ink-faint">{t("privacy")}</p>
            {error && <p role="alert" className="text-red">{error}</p>}
            {state === "sent" && <p role="status" className="font-medium text-green">{t("sent")}</p>}
            <button type="submit" disabled={state === "sending" || text.trim().length < 2} className={buttonStyles.primary}>
              <Send aria-hidden size={22} /> {state === "sending" ? t("sending") : t("send")}
            </button>
          </form>

          <section {...reveal(90)} aria-labelledby="asked-h">
            <h2 id="asked-h" className="font-bn-display text-[24px] leading-tight">{t("listTitle")}</h2>
            {questions.error ? (
              <div className="mt-3"><ErrorState error={questions.error} onRetry={questions.reload} /></div>
            ) : !questions.data ? (
              <Skeleton lines={2} className="mt-3" />
            ) : questions.data.length === 0 ? (
              <p className="mt-3 rounded-card border border-dashed border-rule-strong p-5 text-ink-soft">{t("none")}</p>
            ) : (
              <ol className="mt-3 grid gap-3">
                {questions.data.map((q) => (
                  <li key={q.id} className="rounded-card border border-rule bg-paper-raised p-5">
                    <p className="flex items-start gap-2 text-ink">
                      <UserRound aria-hidden size={20} className="mt-1 shrink-0 text-ink-soft" />
                      <span className="min-w-0 break-words">{q.text}</span>
                    </p>
                    <p className="mt-1 pl-7 text-[15px] text-ink-faint">{t("askedOn", { date: date(q.created_at, locale) })}</p>
                    {q.reply ? (
                      <div className={cx("mt-4 rounded-md border-l-4 border-neel bg-neel-tint/60 p-4", !q.reply_seen_at && "ring-2 ring-neel/30")}>
                        <p className="flex items-center gap-2 text-[15px] font-semibold text-neel">
                          <MessageSquareReply aria-hidden size={18} /> {t("replyFrom", { name: q.replied_by ?? "" })}
                        </p>
                        <p className="mt-1.5 break-words text-ink">{q.reply}</p>
                        <div className="mt-1 flex flex-wrap items-center gap-x-4">
                          <span className="text-[15px] text-ink-faint">{date(q.replied_at, locale)}</span>
                          <ListenButton text={q.reply} />
                        </div>
                      </div>
                    ) : (
                      <p className="mt-3 inline-flex items-center gap-1.5 rounded-chip bg-paper-sunk px-3 py-1 text-[15px] text-ink-soft">
                        <Clock aria-hidden size={15} /> {t("waiting")}
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>
      </main>
    </>
  );
}
