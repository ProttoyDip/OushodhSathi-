"use client";

import { ArrowRight, Phone } from "lucide-react";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { cx } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { SathiMark } from "./SathiMark";

/** The one thing to do next. Chosen by the backend state machine; never a chat bubble. */
export function NextStepCard({ pid }: { pid: number }) {
  const t = useTranslations("sathi");
  const locale = useLocale();
  const step = useApi(() => api.nextStep(pid, locale), [pid, locale], 30000);
  const [phrased, setPhrased] = useState<{ code: string; text: string } | null>(null);

  // the fixed sentence shows at once; a warmer AI wording replaces it only if it passed the checks
  const code = step.data?.code;
  useEffect(() => {
    if (!code || code === "EMERGENCY_ACTIVE") return;
    let live = true;
    api.nextStep(pid, locale, true)
      .then((s) => { if (live && s.code === code && s.phrased_by !== "fixed") setPhrased({ code, text: s.text }); })
      .catch(() => {});
    return () => { live = false; };
  }, [pid, locale, code]);

  const s = step.data;
  if (!s) {
    return <div aria-busy="true" className="h-[148px] rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />;
  }
  const emergency = s.code === "EMERGENCY_ACTIVE";
  const text = phrased?.code === s.code ? phrased.text : s.text;
  const tel = s.route.startsWith("tel:");

  return (
    <section
      aria-labelledby="next-step-h"
      aria-live="polite"
      className={cx(
        "rounded-card border p-5 shadow-soft",
        emergency ? "border-red-line bg-red-tint" : "border-neel/40 bg-paper-raised",
      )}
    >
      <h2 id="next-step-h" className={cx("flex items-center gap-2 text-[15px] font-semibold", emergency ? "text-red" : "text-neel")}>
        <SathiMark size={24} />
        {emergency ? t("urgent") : t("nextStep")}
      </h2>
      <p className={cx("mt-3 font-bn-display text-[24px] leading-[1.35]", emergency ? "text-red" : "text-ink")}>{text}</p>
      {tel ? (
        <a href={s.route} className="press mt-4 inline-flex min-h-14 w-full items-center justify-center gap-2.5 rounded-card bg-red px-6 text-lg font-semibold text-paper">
          <Phone aria-hidden size={22} /> {s.button}
        </a>
      ) : (
        <Link
          href={s.route}
          className="press mt-4 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-card border border-neel bg-paper-raised px-5 text-base font-semibold text-neel transition-colors hover:bg-neel-tint"
        >
          {s.button} <ArrowRight aria-hidden size={20} />
        </Link>
      )}
    </section>
  );
}
