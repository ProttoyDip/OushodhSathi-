"use client";

import { ArrowLeft, Printer } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { buttonStyles, LangToggle, ThemeToggle } from "@/components/Chrome";
import { FamilyKeyFromUrl } from "@/components/FamilyKeyFromUrl";
import { MedicinePassport } from "@/components/MedicinePassport";
import { PassportSettings } from "@/components/PassportSettings";
import { ShareDigest } from "@/components/ShareDigest";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";

export default function PassportPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const t = useTranslations("passport");
  const tc = useTranslations("common");
  const passport = useApi(() => api.passport(pid), [pid]);
  const patient = useApi(() => api.patient(pid), [pid]);
  useEffect(() => {
    if (passport.data) api.seen(pid, "passport").catch(() => {});
  }, [pid, passport.data]);
  // the QR opens the read-only emergency page: undefined while loading, null when switched off
  const [token, setToken] = useState<string | null>();
  useEffect(() => {
    api.emergencyToken(pid).then((r) => setToken(r.token)).catch(() => setToken(null));
  }, [pid]);
  const [origin, setOrigin] = useState("");
  useEffect(() => setOrigin(window.location.origin), []);
  const url = token === undefined || !origin ? undefined : token ? `${origin}/e/${token}` : null;

  return (
    <div className="min-h-dvh text-[18px]">
      <FamilyKeyFromUrl />
      <style>{`@page { size: A5 portrait; margin: 7mm; } @media print { html, body { background: #fff !important; } }`}</style>
      <div className="no-print mx-auto flex max-w-[620px] items-center justify-between gap-2 px-4 pt-3 lg:max-w-[1180px] lg:px-8">
        <Link href={`/p/${pid}`} className="-ml-2 inline-flex h-12 items-center gap-1.5 rounded-chip px-2 font-medium">
          <ArrowLeft aria-hidden size={22} />
          {tc("back")}
        </Link>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <LangToggle />
        </div>
      </div>
      {/* phone: one column. desktop: the card on the left, printing and its settings beside it */}
      <main className="mx-auto max-w-[620px] px-4 pb-12 pt-4 lg:max-w-[1180px] lg:px-8 lg:pt-6 print:max-w-none print:p-0">
        {passport.error ? (
          <ErrorState error={passport.error} onRetry={passport.reload} />
        ) : !passport.data ? (
          <Skeleton lines={5} />
        ) : (
          <div className="grid grid-cols-[minmax(0,1fr)] lg:grid-cols-[minmax(0,1fr)_minmax(320px,400px)] lg:items-start lg:gap-10 print:block">
            <MedicinePassport passport={passport.data} url={url} wide />
            <aside className="no-print mt-6 lg:sticky lg:top-6 lg:mt-0 lg:max-h-[calc(100dvh-3rem)] lg:overflow-y-auto lg:overscroll-contain lg:pb-2">
              <button type="button" onClick={() => window.print()} className={buttonStyles.primary}>
                <Printer aria-hidden size={22} />
                {t("print")}
              </button>
              <p className="mt-2 px-1 text-base text-ink-soft">{t("printHint")}</p>
              <ShareDigest pid={pid} className="mt-6" />
              {/* remount once the patient loads so the contact fields start filled in */}
              <PassportSettings
                key={patient.data ? "loaded" : "loading"}
                pid={pid}
                passport={passport.data}
                patient={patient.data}
                token={token}
                onToken={setToken}
                onChanged={passport.reload}
              />
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
