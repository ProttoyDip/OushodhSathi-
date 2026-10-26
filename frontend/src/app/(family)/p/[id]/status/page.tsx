"use client";

import { Camera, Check, Info, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { buttonStyles, FamilyHeader } from "@/components/Chrome";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { cx } from "@/lib/format";
import { useApi } from "@/lib/useApi";

/** Family-safe status: says a review is happening, never what is pending. */
export default function StatusPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const t = useTranslations("status");
  const tc = useTranslations("common");
  const th = useTranslations("home");
  const patient = useApi(() => api.patient(pid), [pid]);
  const status = useApi(() => api.status(pid), [pid], 5000);
  const s = status.data;
  const done = s?.review_state === "reviewed";
  const current = !s ? 1 : done ? 3 : s.review_state === "in_review" ? 1 : 0;
  const steps = [t("stepSent"), t("stepReview"), t("stepReady")];

  return (
    <>
      <FamilyHeader back={`/p/${pid}`} demo={patient.data?.is_demo} />
      <main className="mx-auto w-full max-w-[480px] px-4 pb-12 pt-4">
        {status.error ? (
          <ErrorState error={status.error} onRetry={status.reload} />
        ) : !s ? (
          <Skeleton lines={2} />
        ) : s.review_state === "not_checked" ? (
          <>
            <h1 className="font-bn-display text-[32px] leading-[1.2]">{t("notSent")}</h1>
            <Link href={`/p/${pid}/scan`} className={`${buttonStyles.primary} mt-8`}>
              <Camera aria-hidden size={22} />
              {th("scanCta")}
            </Link>
          </>
        ) : (
          <>
            <h1 className="font-bn-display text-[32px] leading-[1.2]">{done ? t("doneTitle") : t("title")}</h1>
            <p className="mt-3">{done ? t("doneBody") : t("body")}</p>

            <ol className="mt-8 grid gap-0" aria-label={t("title")}>
              {steps.map((label, i) => {
                const complete = i < current || (done && i === 2);
                const active = i === current && !done;
                return (
                  <li key={label} className="grid grid-cols-[40px_1fr] gap-3">
                    <div className="flex flex-col items-center">
                      <span
                        className={cx(
                          "flex h-10 w-10 items-center justify-center rounded-full border-2",
                          complete ? "border-neel bg-neel text-on-neel" : active ? "border-neel bg-paper-raised" : "border-rule bg-paper-raised",
                        )}
                      >
                        {complete ? (
                          <Check aria-hidden size={20} strokeWidth={3} />
                        ) : active ? (
                          <span className="block h-3 w-3 rounded-full bg-neel" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />
                        ) : null}
                      </span>
                      {i < steps.length - 1 && <span aria-hidden className={cx("my-1 w-0.5 flex-1", i < current ? "bg-neel" : "bg-rule")} style={{ minHeight: 28 }} />}
                    </div>
                    <p className={cx("pb-6 pt-1.5", active ? "font-semibold text-ink" : complete ? "text-ink" : "text-ink-faint")}>
                      <span className="sr-only">{complete ? "✓ " : active ? "… " : ""}</span>
                      {label}
                    </p>
                  </li>
                );
              })}
            </ol>

            {done ? (
              <Link href={`/p/${pid}/results`} className={buttonStyles.primary}>
                <ShieldCheck aria-hidden size={22} />
                {th("seeResults")}
              </Link>
            ) : (
              <p className="text-base text-ink-faint">{t("autoRefresh")}</p>
            )}

            <aside className="mt-8 flex gap-3 rounded-card border border-rule bg-paper-raised p-5">
              <Info aria-hidden size={22} className="mt-0.5 shrink-0 text-neel" />
              <p className="text-base text-ink-soft">{t("why")}</p>
            </aside>
            <p className="mt-6 rounded-card border border-rule-strong p-4 font-semibold">{tc("safety")}</p>
          </>
        )}
      </main>
    </>
  );
}
