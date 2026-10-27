import { cx } from "@/lib/format";

/** Sathi's monogram: the Bangla letters "সা" on indigo. No robot, no sparkles. */
export function SathiMark({ size = 28, className }: { size?: number; className?: string }) {
  return (
    <span
      aria-hidden
      className={cx("inline-flex shrink-0 items-center justify-center rounded-full bg-neel font-bn-display font-semibold leading-none text-on-neel", className)}
      style={{ width: size, height: size, fontSize: Math.round(size * 0.5), paddingTop: Math.round(size * 0.06) }}
    >
      সা
    </span>
  );
}
