"use client";

import { CloudOff, RotateCw } from "lucide-react";
import { useTranslations } from "next-intl";
import type { ApiError } from "@/lib/api";
import { buttonStyles } from "./Chrome";

export function ErrorState({ error, onRetry }: { error: ApiError; onRetry?: () => void }) {
  const t = useTranslations("common");
  const message = error.status === 0 ? t("errorOffline") : error.status === 404 ? t("errorNotFound") : error.status === 429 ? t("errorTooMany") : t("errorGeneric");
  return (
    <div role="alert" className="rounded-card border border-rule bg-paper-raised p-5">
      <CloudOff aria-hidden size={28} className="text-ink-soft" />
      <p className="mt-3 text-lg text-ink">{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className={`${buttonStyles.secondary} mt-4`}>
          <RotateCw aria-hidden size={18} />
          {t("retry")}
        </button>
      )}
    </div>
  );
}

/** Calm placeholder blocks with fixed heights, so nothing jumps when data lands. */
export function Skeleton({ lines = 3, className = "" }: { lines?: number; className?: string }) {
  const t = useTranslations("common");
  return (
    <div className={`grid gap-3 ${className}`} aria-busy="true" aria-label={t("loading")}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-20 rounded-card bg-paper-sunk"
          style={{ animation: `breathe 1.6s ease-in-out ${i * 120}ms infinite` }}
        />
      ))}
    </div>
  );
}
