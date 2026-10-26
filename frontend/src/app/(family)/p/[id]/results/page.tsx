"use client";

import { BookUser, CircleCheck, ScanLine } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { FlagResult } from "@/components/FlagResult";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";

/** Only CONFIRMED findings, straight from the family view of the API. */
export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const t = useTranslations("results");
  const patient = useApi(() => api.patient(pid), [pid]);
  const status = useApi(() => api.status(pid), [pid]);
  const flags = useApi(() => api.familyFlags(pid), [pid]);
  const list = flags.data ?? [];
  const reviewed = status.data?.review_state === "reviewed";

  return (
    <>
      <FamilyHeader back={`/p/${pid}`} demo={patient.data?.is_demo} />
      <main className={`mx-auto w-full px-4 pb-12 pt-4 lg:pt-8 ${familyWidth}`}>
        <div className="lg:flex lg:items-end lg:justify-between lg:gap-8">
          <div>
            <h1 className="font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t("title")}</h1>
            {list.length > 0 && <p className="mt-2 text-ink-soft">{t("intro")}</p>}
          </div>
          {list.length > 0 && (
            <Link href={`/passport/${pid}`} className={`${buttonStyles.secondary} hidden shrink-0 lg:inline-flex`}>
              <BookUser aria-hidden size={20} />
              {t("bringPassport")}
            </Link>
          )}
        </div>

        {flags.error ? (
          <div className="mt-6"><ErrorState error={flags.error} onRetry={flags.reload} /></div>
        ) : !flags.data || !status.data ? (
          <Skeleton lines={3} className="mt-6" />
        ) : list.length === 0 && reviewed ? (
          <section className="mt-6 rounded-card border border-green-line bg-green-tint p-6 text-center lg:mx-auto lg:max-w-[560px]" style={{ animation: "settle 240ms var(--ease-out-quint) both" }}>
            <CircleCheck aria-hidden size={56} strokeWidth={1.75} className="mx-auto text-green" />
            <h2 className="mt-3 font-bn-display text-[26px] leading-tight text-ink">{t("noneTitle")}</h2>
            <p className="mt-2 text-ink-soft">{t("noneBody")}</p>
            <Link href={`/passport/${pid}`} className={`${buttonStyles.primary} mt-6`}>
              <BookUser aria-hidden size={22} />
              {t("bringPassport")}
            </Link>
          </section>
        ) : list.length === 0 ? (
          <section className="mt-6 rounded-card border border-rule bg-paper-raised p-6 lg:max-w-[560px]">
            <ScanLine aria-hidden size={32} className="text-neel" />
            <h2 className="mt-3 font-bn-display text-[24px] leading-tight">{t("pendingTitle")}</h2>
            <p className="mt-2 text-ink-soft">{t("pendingBody")}</p>
          </section>
        ) : (
          <>
            <div className="mt-6 grid grid-cols-[minmax(0,1fr)] gap-5">
              {list.map((f, i) => (
                <FlagResult key={f.id} flag={f} style={{ animation: `settle 240ms var(--ease-out-quint) ${i * 120}ms both` }} />
              ))}
            </div>
            <Link href={`/passport/${pid}`} className={`${buttonStyles.secondary} mt-8 w-full lg:hidden`}>
              <BookUser aria-hidden size={20} />
              {t("bringPassport")}
            </Link>
          </>
        )}
      </main>
    </>
  );
}
