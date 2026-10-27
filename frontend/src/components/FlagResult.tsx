"use client";

import { MessageSquareQuote } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import type { CSSProperties } from "react";
import { date, genericName } from "@/lib/format";
import type { Flag } from "@/lib/types";
import { DuplicateConnector } from "./DuplicateConnector";
import { SeverityBadge } from "./SeverityBadge";
import { StripCard } from "./StripCard";

/** One CONFIRMED finding as the family sees it. Never render a pending flag with this. */
export function FlagResult({ flag, style, animate = true }: { flag: Flag; style?: CSSProperties; animate?: boolean }) {
  const t = useTranslations();
  const locale = useLocale();
  if (flag.status !== "confirmed") return null; // belt and braces; the API already filters

  const generic = (flag.meta.generic as string | undefined) ?? flag.items[0]?.generic ?? "";
  const pairLabel =
    flag.code === "DUPLICATE_GENERIC"
      ? t(flag.items.length > 2 ? "connector.all" : "connector.both", { generic: genericName(generic, locale) })
      : flag.code === "INTERACTION"
        ? t("connector.together")
        : t(`flagTitle.${flag.code}`);
  const explanation = locale === "bn" ? flag.explanation_bn ?? flag.evidence : flag.evidence;
  const safety = t("common.safety");
  // the fixed safety sentence is shown once, separately, below the note
  const body = explanation.replace(safety, "").trim();

  return (
    <article
      style={style}
      aria-labelledby={`flag-${flag.id}`}
      className="@container min-w-0 rounded-card border border-rule bg-paper-raised p-5 shadow-soft @3xl:p-7"
    >
      <header className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <SeverityBadge severity={flag.severity} />
        <h2 id={`flag-${flag.id}`} className="font-bn-display text-[24px] leading-tight text-ink">
          {t(`flagTitle.${flag.code}`)}
        </h2>
      </header>

      {/* narrow: stacked. wide card (desktop): strips on the left, words on the right */}
      <div className="mt-5 grid grid-cols-[minmax(0,1fr)] gap-5 @3xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] @3xl:gap-8">
      <div>
        {flag.items.length >= 2 ? (
          <DuplicateConnector label={pairLabel} tone={flag.severity} animate={animate}>
            {flag.items.map((it) => (
              <StripCard key={it.id} item={{ ...it, confirmed: true }} density="compact" highlight={flag.severity} />
            ))}
          </DuplicateConnector>
        ) : (
          flag.items.map((it) => (
            <StripCard key={it.id} item={{ ...it, confirmed: true }} density="compact" highlight={flag.severity} />
          ))
        )}
      </div>

      <div>
      <p className="text-ink">{body}</p>

      {flag.note && (
        <figure className="mt-4 rounded-card bg-paper-sunk p-4">
          <figcaption className="flex items-center gap-2 text-base font-semibold text-ink-soft">
            <MessageSquareQuote aria-hidden size={18} />
            {t("results.noteFrom", { name: flag.reviewer ?? "" })}
          </figcaption>
          <blockquote className="mt-1.5 text-ink">{flag.note}</blockquote>
          {flag.reviewed_at && (
            <p className="mt-1.5 text-sm text-ink-faint">{t("results.reviewedOn", { date: date(flag.reviewed_at, locale) })}</p>
          )}
        </figure>
      )}

      <p className="mt-4 border-t border-rule pt-4 font-semibold text-ink">{safety}</p>
      </div>
      </div>
    </article>
  );
}
