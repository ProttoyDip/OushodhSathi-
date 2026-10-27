"use client";

import { ArrowLeft, Printer } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { buttonStyles, LangToggle, ThemeToggle } from "@/components/Chrome";
import { FamilyKeyFromUrl } from "@/components/FamilyKeyFromUrl";
import { MedicinePassport } from "@/components/MedicinePassport";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { familyLink } from "@/lib/familyKey";
import { useApi } from "@/lib/useApi";

export default function PassportPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const t = useTranslations("passport");
  const tc = useTranslations("common");
  const passport = useApi(() => api.passport(pid), [pid]);
  useEffect(() => {
    if (passport.data) api.seen(pid, "passport").catch(() => {});
  }, [pid, passport.data]);
  const [url, setUrl] = useState<string>();
  // the QR opens this household's own passport: a private link when this browser holds the family key
  useEffect(() => setUrl(familyLink(pid, `/passport/${pid}`) ?? `${window.location.origin}/passport/${pid}`), [pid]);

  return (
    <div className="min-h-dvh text-[18px]">
      <FamilyKeyFromUrl />
      <style>{`@page { size: A5 portrait; margin: 7mm; } @media print { html, body { background: #fff !important; } }`}</style>
      <div className="no-print mx-auto flex max-w-[620px] items-center justify-between gap-2 px-4 pt-3">
        <Link href={`/p/${pid}`} className="-ml-2 inline-flex h-12 items-center gap-1.5 rounded-chip px-2 font-medium">
          <ArrowLeft aria-hidden size={22} />
          {tc("back")}
        </Link>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <LangToggle />
        </div>
      </div>
      <main className="mx-auto max-w-[620px] px-4 pb-12 pt-4 print:max-w-none print:p-0">
        {passport.error ? (
          <ErrorState error={passport.error} onRetry={passport.reload} />
        ) : !passport.data ? (
          <Skeleton lines={5} />
        ) : (
          <>
            <MedicinePassport passport={passport.data} url={url} />
            {url?.includes("key=") && <p className="no-print mt-4 text-base text-ink-soft">{t("qrPrivate")}</p>}
            <button type="button" onClick={() => window.print()} className={`${buttonStyles.primary} no-print mt-6`}>
              <Printer aria-hidden size={22} />
              {t("print")}
            </button>
          </>
        )}
      </main>
    </div>
  );
}
