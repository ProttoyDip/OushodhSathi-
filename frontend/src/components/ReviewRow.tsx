"use client";

import { Clock3, Pill, Stethoscope, UserRound } from "lucide-react";
import { useTranslations } from "next-intl";
import { forwardRef } from "react";
import { cx, since } from "@/lib/format";
import type { Flag } from "@/lib/types";
import { SeverityBadge } from "./SeverityBadge";

/** The rule's short name in the current language. */
export function useRuleName() {
  const t = useTranslations("review.rules");
  return (code: Flag["code"]) => t(code);
}

/** One row of the reviewer queue: severity, rule, medicines, patient age, time waiting. */
export const ReviewRow = forwardRef<
  HTMLButtonElement,
  { flag: Flag; selected?: boolean; onSelect?: () => void; now?: number }
>(function ReviewRow({ flag, selected, onSelect, now }, ref) {
  const brands = flag.items.map((i) => i.brand).join(" + ");
  const t = useTranslations("review");
  const ruleName = useRuleName();
  return (
    <button
      ref={ref}
      type="button"
      role="option"
      aria-selected={selected}
      onClick={onSelect}
      className={cx(
        "group grid w-full grid-cols-[1fr_auto] gap-x-3 gap-y-1.5 rounded-card border px-3.5 py-3 text-left transition-colors duration-150",
        selected
          ? "border-neel bg-paper-raised shadow-soft"
          : "border-transparent hover:border-rule hover:bg-paper-raised/70",
      )}
    >
      <div className="flex min-w-0 items-center gap-2">
        <SeverityBadge
          severity={flag.severity}
          size="sm"
          label={flag.severity === "red" ? t("dash.red") : t("dash.amber")}
        />
        <span className="truncate text-[15px] font-semibold text-ink">{ruleName(flag.code)}</span>
      </div>
      <span className="tabular flex items-center gap-1 self-center text-[13px] text-ink-faint" title={t("row.waiting")}>
        <Clock3 aria-hidden size={13} />
        {since(flag.created_at, now)}
      </span>
      <div className="col-span-2 flex min-w-0 items-center gap-3 text-[13px] text-ink-soft">
        <span className="flex min-w-0 items-center gap-1">
          <Pill aria-hidden size={13} className="shrink-0" />
          <span className="truncate">{brands || "—"}</span>
        </span>
        {flag.patient && (
          <span className="tabular flex shrink-0 items-center gap-1">
            <UserRound aria-hidden size={13} />
            {t("row.age", { age: flag.patient.age })}
          </span>
        )}
        <span className="flex shrink-0 items-center gap-1">
          <Stethoscope aria-hidden size={13} />
          {t(`routes.${flag.routed_to}`)}
        </span>
      </div>
    </button>
  );
});
