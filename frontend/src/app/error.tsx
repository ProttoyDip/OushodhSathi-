"use client";

import { Home, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Wordmark } from "@/components/BrandMark";

/** A page crashed while rendering. Nothing about the household is shown here. */
export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const t = useTranslations("errors");
  return (
    <main className="mx-auto flex min-h-dvh max-w-[560px] flex-col justify-center px-6 py-16">
      <Link href="/" className="w-fit"><Wordmark /></Link>
      <h1 className="mt-10 font-display text-[36px] leading-[1.1] text-ink">{t("errorTitle")}</h1>
      <p className="mt-3 text-lg text-ink-soft">{t("errorBody")}</p>
      <div className="mt-8 flex flex-wrap gap-3">
        <button type="button" onClick={reset} className="press inline-flex min-h-14 items-center gap-2.5 rounded-card bg-neel px-6 text-lg font-semibold text-on-neel hover:bg-neel-hover">
          <RotateCcw aria-hidden size={20} /> {t("retry")}
        </button>
        <Link href="/" className="press inline-flex min-h-14 items-center gap-2 rounded-card border border-rule-strong bg-paper-raised px-6 text-lg font-semibold text-ink">
          <Home aria-hidden size={20} /> {t("home")}
        </Link>
      </div>
    </main>
  );
}
