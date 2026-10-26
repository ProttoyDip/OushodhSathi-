import { cx } from "@/lib/format";

/** A cut piece of blister strip: the product's mark. Authored SVG, one stroke weight. */
export function BrandMark({ size = 28, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      aria-hidden
      className={cx("shrink-0", className)}
    >
      <rect x="3" y="7" width="26" height="18" rx="3" fill="var(--foil)" stroke="var(--ink)" strokeWidth="1.6" />
      <circle cx="11" cy="16" r="4.2" fill="var(--foil-hi)" stroke="var(--ink)" strokeWidth="1.6" />
      <circle cx="21" cy="16" r="4.2" fill="var(--neel)" stroke="var(--ink)" strokeWidth="1.6" />
      <path d="M29 9.5v2M29 14.5v3M29 20.5v2" stroke="var(--paper)" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export function Wordmark({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cx("inline-flex items-center gap-2 text-ink", className)}>
      <BrandMark />
      <span className="flex items-baseline gap-2">
        <span lang="bn" className="font-bn-display text-[22px] leading-none">ওষুধসাথী</span>
        {!compact && (
          <span lang="en" className="hidden font-display text-[19px] italic leading-none text-ink-soft sm:inline">OushodhSathi</span>
        )}
      </span>
    </span>
  );
}
