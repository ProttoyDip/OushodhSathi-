"use client";

import { CalendarClock, CircleHelp, ExternalLink, Globe, ScanEye, Stethoscope } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import type { CSSProperties, ReactNode } from "react";
import { cx, expiry, genericName, num } from "@/lib/format";
import type { MedicineItem } from "@/lib/types";

type StripItem = Pick<
  MedicineItem,
  "brand" | "strength" | "expiry" | "prescriber" | "confidence" | "generic" | "match_method" | "match_source"
> & { thumbnail?: string | null; needs_review?: boolean; confirmed?: boolean };

const LOW = 0.75;

/**
 * A piece of medicine strip lying on prescription paper: foil band with blister
 * domes on the left, punched perforation on the right edge.
 */
export function StripCard({
  item,
  children,
  density = "comfortable",
  className,
  style,
  highlight,
}: {
  item: StripItem;
  children?: ReactNode;
  density?: "comfortable" | "compact";
  className?: string;
  style?: CSSProperties;
  highlight?: "red" | "amber";
}) {
  const t = useTranslations("strip");
  const locale = useLocale();
  const low = item.confidence < LOW;
  const web = item.match_method === "web_unverified";
  const unknown = item.match_method === "not_found" || !item.generic;
  const needsCheck = !item.confirmed && (low || web || unknown);
  const compact = density === "compact";
  const pct = Math.round(item.confidence * 100);

  return (
    <article
      style={style}
      className={cx(
        "relative flex overflow-hidden rounded-card bg-paper-raised text-ink",
        needsCheck ? "border-2 border-dashed border-amber" : "border border-rule shadow-soft",
        highlight === "red" && !needsCheck && "border-red-line",
        highlight === "amber" && !needsCheck && "border-amber-line",
        className,
      )}
    >
      {/* foil band */}
      <div
        aria-hidden
        className={cx("foil flex shrink-0 flex-col items-center justify-center gap-2 border-r border-foil-lo", compact ? "w-11" : "w-14")}
      >
        {[0, 1].map((i) => (
          <span
            key={i}
            className={cx("block rounded-full border border-foil-lo", compact ? "h-[18px] w-[18px]" : "h-6 w-6")}
            style={{
              background: "radial-gradient(circle at 34% 30%, var(--foil-hi), var(--foil) 58%, var(--foil-lo))",
              boxShadow: "inset 0 -2px 3px rgb(0 0 0 / 0.16), 0 1px 0 rgb(255 255 255 / 0.4)",
            }}
          />
        ))}
      </div>

      <div className={cx("min-w-0 flex-1", compact ? "p-3 pr-5" : "p-4 pr-6")}>
        {/* the photo floats so the ingredient chip can drop below it when the column is narrow */}
        <div className="flow-root">
          {item.thumbnail && (
            // eslint-disable-next-line @next/next/no-img-element -- short-lived data URL, never stored
            <img
              src={item.thumbnail}
              alt={t("photo", { brand: item.brand })}
              className={cx("float-right ml-3 mb-2 rounded-md border border-rule object-cover", compact ? "h-12 w-12" : "h-16 w-16")}
            />
          )}
          <div className="min-w-0">
            <h3 className={cx("flex flex-wrap items-baseline gap-x-2 font-semibold leading-tight", compact ? "text-lg" : "text-[22px]")}>
              <span className="break-words">{item.brand}</span>
              {item.strength && (
                <span className={cx("tabular font-medium text-ink-soft", compact ? "text-[15px]" : "text-lg")}>{item.strength}</span>
              )}
            </h3>
            <div className="mt-2">
              {item.generic ? (
                <span
                  className={cx(
                    "inline-flex max-w-full items-center rounded-2xl border px-3 py-1 font-medium leading-snug",
                    compact ? "min-h-7 text-sm" : "min-h-8 text-[15px]",
                    highlight === "red"
                      ? "border-red-line bg-red-tint text-red"
                      : highlight === "amber"
                        ? "border-amber-line bg-amber-tint text-amber"
                        : "border-rule bg-neel-tint text-ink",
                  )}
                >
                  {genericName(item.generic, locale)}
                </span>
              ) : (
                <span className="inline-flex min-h-8 max-w-full items-center gap-1.5 rounded-2xl border border-rule px-3 py-1 text-[15px] leading-snug text-ink-soft">
                  <CircleHelp aria-hidden size={16} className="shrink-0" /> {t("unknownGeneric")}
                </span>
              )}
            </div>
          </div>
        </div>

        <dl className={cx("mt-3 flex flex-wrap gap-x-4 gap-y-1 text-ink-soft", compact ? "text-sm" : "text-base")}>
          <div className="flex items-center gap-1.5">
            <CalendarClock aria-hidden size={16} className="shrink-0" />
            <dt className="sr-only">{t("expiry")}</dt>
            <dd className="tabular">
              {item.expiry ? `${t("expiry")} ${expiry(item.expiry, locale)}` : t("noExpiry")}
            </dd>
          </div>
          {item.prescriber && (
            <div className="flex min-w-0 max-w-full items-center gap-1.5">
              <Stethoscope aria-hidden size={16} className="shrink-0 self-start mt-1" />
              <dt className="sr-only">{t("prescriber")}</dt>
              <dd className="min-w-0 break-words leading-snug">{item.prescriber}</dd>
            </div>
          )}
        </dl>

        {/* confidence */}
        <div className="mt-3 flex items-center gap-3">
          <span className={cx("shrink-0 text-ink-faint", compact ? "text-[13px]" : "text-sm")}>{t("confidence")}</span>
          <div
            role="meter"
            aria-label={t("confidence")}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={pct}
            className="h-1.5 flex-1 overflow-hidden rounded-chip bg-paper-sunk"
          >
            <div className={cx("h-full rounded-chip", low ? "bg-amber" : "bg-neel")} style={{ width: `${pct}%` }} />
          </div>
          <span className={cx("tabular shrink-0 font-medium", low ? "text-amber" : "text-ink-soft", compact ? "text-[13px]" : "text-sm")}>
            {num(pct, locale)}%
          </span>
        </div>

        {needsCheck && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {(low || unknown) && !web && (
              <span className="inline-flex min-h-8 max-w-full items-center gap-1.5 rounded-2xl border border-amber-line bg-amber-tint px-3 py-1 text-[15px] font-semibold leading-snug text-amber">
                <ScanEye aria-hidden size={16} className="shrink-0" />
                {unknown ? t("notFound") : t("checkPlease")}
              </span>
            )}
            {web && (
              <span className="inline-flex min-h-8 max-w-full items-center gap-1.5 rounded-2xl border border-amber-line bg-amber-tint px-3 py-1 text-[15px] font-semibold leading-snug text-amber">
                <Globe aria-hidden size={16} className="shrink-0" />
                {t("webUnverified")}
              </span>
            )}
            {web && item.match_source && (
              <a
                href={item.match_source}
                target="_blank"
                rel="noreferrer"
                className="inline-flex min-h-8 items-center gap-1 text-sm text-ink-soft underline"
              >
                {t("source")}: {safeHost(item.match_source)} <ExternalLink aria-hidden size={13} />
              </a>
            )}
          </div>
        )}

        {children && <div className="mt-4">{children}</div>}
      </div>

      {/* punched perforation on the cut edge */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-y-0 right-0 w-[7px]"
        style={{
          backgroundImage: "radial-gradient(circle at 100% 50%, var(--paper) 3.4px, transparent 3.9px)",
          backgroundSize: "100% 14px",
          backgroundRepeat: "repeat-y",
        }}
      />
    </article>
  );
}

function safeHost(url: string) {
  try {
    return new URL(url).host;
  } catch {
    return url;
  }
}
