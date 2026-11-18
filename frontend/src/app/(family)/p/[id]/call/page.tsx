"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { CallSimulator } from "@/components/calls/CallSimulator";
import { WhatsAppSimulator } from "@/components/calls/WhatsAppSimulator";
import { FamilyHeader, familyWidth } from "@/components/Chrome";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { reveal } from "@/lib/reveal";
import { useApi } from "@/lib/useApi";

/** Try the daily check-in call in the browser (the simulator: no phone number, nothing dials). */
export default function CallPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const t = useTranslations("calls");
  const settings = useApi(() => api.callSettings(pid), [pid]);
  const wa = settings.data?.channel === "whatsapp";

  return (
    <>
      <FamilyHeader back={`/p/${pid}`} />
      <main className={`mx-auto w-full px-4 pb-16 pt-4 lg:pt-8 ${familyWidth}`}>
        <h1 {...reveal(0)} className="font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t(wa ? "titleWhatsapp" : "title")}</h1>
        <p className="mt-2 max-w-[60ch] text-ink-soft">{t(wa ? "introWhatsapp" : "intro")}</p>
        <div className="mt-6">
          {settings.error ? (
            <ErrorState error={settings.error} onRetry={settings.reload} />
          ) : !settings.data ? (
            <Skeleton />
          ) : !settings.data.active ? (
            <p className="rounded-card border border-rule bg-paper p-4 text-ink-soft">
              {t("off")} <Link href={`/p/${pid}/settings#calls`} className="font-semibold text-neel underline">{t("turnOn")}</Link>
            </p>
          ) : settings.data.approved_slots.length === 0 ? (
            <p className="rounded-card border border-rule bg-paper p-4 text-ink-soft">{t("noTimes")}</p>
          ) : (
            settings.data.channel === "whatsapp" ? <WhatsAppSimulator pid={pid} /> : <CallSimulator pid={pid} />
          )}
        </div>
      </main>
    </>
  );
}
