"use client";

import { Link2 } from "lucide-react";
import { Children, type CSSProperties, type ReactNode } from "react";
import { cx } from "@/lib/format";

/**
 * The hero moment: StripCards that share a generic slide together and a bracket
 * draws itself between them, labelled e.g. "দুটোই প্যারাসিটামল".
 *
 * vertical   — phone: cards stacked, bracket on the left, label on the seam.
 * horizontal — desktop: cards side by side, bracket across the top, label on it.
 */
export function DuplicateConnector({
  children,
  label,
  tone = "red",
  orientation = "vertical",
  animate = true,
  delay = 0,
  className,
}: {
  children: ReactNode;
  label: string;
  tone?: "red" | "amber";
  orientation?: "vertical" | "horizontal";
  animate?: boolean;
  delay?: number;
  className?: string;
}) {
  const cards = Children.toArray(children);
  const stroke = tone === "red" ? "var(--red)" : "var(--amber)";
  const pill =
    tone === "red" ? "bg-red text-paper-raised border-red" : "bg-amber text-paper-raised border-amber";
  const anim = (name: string, ms: number, extra = 0): CSSProperties | undefined =>
    animate ? { animation: `${name} ${ms}ms var(--ease-out-quint) ${delay + extra}ms both` } : undefined;

  if (orientation === "horizontal") {
    return (
      <div className={cx("relative pt-10", className)} role="group" aria-label={label}>
        <svg
          aria-hidden
          className="absolute inset-x-[12%] top-3 h-6 w-[76%] overflow-visible"
          viewBox="0 0 100 20"
          preserveAspectRatio="none"
          style={anim("reveal-x", 320, 200)}
        >
          <path
            d="M1 20 V6 H99 V20"
            fill="none"
            stroke={stroke}
            strokeWidth={2.5}
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        <span
          className={cx(
            "absolute left-1/2 top-0 z-10 inline-flex h-9 items-center gap-2 rounded-chip border px-4 text-[15px] font-semibold whitespace-nowrap shadow-soft",
            pill,
          )}
          style={{ transform: "translateX(-50%)", ...(animate ? { animation: `label-in-x 220ms var(--ease-out-quint) ${delay + 420}ms both` } : {}) }}
        >
          <Link2 aria-hidden size={17} strokeWidth={2.5} />
          {label}
        </span>
        <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${cards.length}, minmax(0, 1fr))` }}>
          {cards.map((card, i) => (
            <div
              key={i}
              style={i === 0 ? anim("snap-left", 260) : i === cards.length - 1 ? anim("snap-right", 260) : undefined}
            >
              {card}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cx("relative min-w-0 pl-6", className)} role="group" aria-label={label}>
      <svg
        aria-hidden
        className="absolute left-0 top-10 h-[calc(100%-5rem)] w-5 overflow-visible"
        viewBox="0 0 20 100"
        preserveAspectRatio="none"
        style={anim("reveal-y", 320, 200)}
      >
        <path
          d="M20 1 H5 V99 H20"
          fill="none"
          stroke={stroke}
          strokeWidth={2.5}
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <div className="flex min-w-0 flex-col gap-3">
        {cards.map((card, i) => (
          <div
            key={i}
            className="min-w-0"
            style={i === 0 ? anim("snap-top", 260) : i === cards.length - 1 ? anim("snap-bottom", 260) : undefined}
          >
            {card}
          </div>
        ))}
      </div>
      <span
        className={cx(
          "absolute left-[5px] top-1/2 z-10 inline-flex h-9 items-center gap-2 rounded-chip border px-3.5 text-[15px] font-semibold whitespace-nowrap shadow-soft",
          pill,
        )}
        style={{ transform: "translateY(-50%)", ...(animate ? { animation: `label-in-seam 220ms var(--ease-out-quint) ${delay + 420}ms both` } : {}) }}
      >
        <Link2 aria-hidden size={17} strokeWidth={2.5} />
        {label}
      </span>
    </div>
  );
}
