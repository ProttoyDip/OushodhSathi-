"use client";

import { CircleCheck, OctagonAlert, TriangleAlert } from "lucide-react";
import { useTranslations } from "next-intl";
import { cx } from "@/lib/format";

export type BadgeSeverity = "red" | "amber" | "green";

const TONE: Record<BadgeSeverity, string> = {
  red: "text-red bg-red-tint border-red-line",
  amber: "text-amber bg-amber-tint border-amber-line",
  green: "text-green bg-green-tint border-green-line",
};
const ICON = { red: OctagonAlert, amber: TriangleAlert, green: CircleCheck };
const SIZE = {
  sm: { box: "h-7 gap-1.5 px-2.5 text-[13px]", icon: 15 },
  md: { box: "h-9 gap-2 px-3 text-[15px]", icon: 18 },
  lg: { box: "h-12 gap-2.5 px-4 text-lg", icon: 22 },
};

/** Severity is always colour + icon + word, never colour alone. */
export function SeverityBadge({
  severity,
  size = "md",
  label,
  className,
}: {
  severity: BadgeSeverity;
  size?: keyof typeof SIZE;
  label?: string;
  className?: string;
}) {
  const t = useTranslations("severity");
  const Icon = ICON[severity];
  const s = SIZE[size];
  return (
    <span
      className={cx(
        "inline-flex shrink-0 items-center rounded-chip border font-semibold leading-none whitespace-nowrap",
        TONE[severity],
        s.box,
        className,
      )}
    >
      <Icon aria-hidden size={s.icon} strokeWidth={2.25} />
      <span>{label ?? t(severity)}</span>
    </span>
  );
}
