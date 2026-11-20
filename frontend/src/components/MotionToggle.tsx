"use client";

import { Pause, Play } from "lucide-react";
import { useTranslations } from "next-intl";
import { usePauseMotion } from "@/lib/motionPref";
import { cx } from "@/lib/format";

/** The site-wide "Pause motion" switch, remembered on this device. Hidden when the OS already asks
 * for reduced motion (then nothing moves and there is nothing to pause). */
export function MotionToggle({ className }: { className?: string }) {
  const t = useTranslations("common");
  const { paused, reducedByOs, setPaused } = usePauseMotion();
  if (reducedByOs) return null;
  return (
    <button
      type="button"
      aria-pressed={paused}
      onClick={() => setPaused(!paused)}
      title={paused ? t("motionPlay") : t("motionPause")}
      className={cx(
        "press inline-flex h-12 items-center gap-2 whitespace-nowrap rounded-chip border border-rule bg-paper-raised px-3 text-[15px] font-medium text-ink transition-colors hover:border-rule-strong",
        className,
      )}
    >
      {paused ? <Play aria-hidden size={17} /> : <Pause aria-hidden size={17} />}
      <span className="sr-only sm:not-sr-only">{paused ? t("motionPlay") : t("motionPause")}</span>
    </button>
  );
}
