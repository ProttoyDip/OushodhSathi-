"use client";

import { MotionConfig, type Transition } from "motion/react";
import type { ReactNode } from "react";
import { usePauseMotion } from "@/lib/motionPref";

/** One spring for the whole product: quick to settle, no wobble. */
export const SPRING: Transition = { type: "spring", stiffness: 420, damping: 38, mass: 0.9 };
/** Slower spring for large travel (cards moving between layouts). */
export const SPRING_TRAVEL: Transition = { type: "spring", stiffness: 260, damping: 32, mass: 1 };

/** Honours prefers-reduced-motion and the site-wide "Pause motion" switch everywhere motion is used. */
export function MotionProvider({ children }: { children: ReactNode }) {
  const { paused } = usePauseMotion();
  return (
    <MotionConfig reducedMotion={paused ? "always" : "user"} transition={SPRING}>
      {children}
    </MotionConfig>
  );
}
