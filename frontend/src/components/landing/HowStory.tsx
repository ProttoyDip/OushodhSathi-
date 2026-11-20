"use client";

import { ListChecks, ScanText, Stethoscope, Users } from "lucide-react";
import { useMotionValueEvent, useScroll } from "motion/react";
import { useRef, useState, type ReactNode } from "react";

type Actor = "family" | "ai" | "rules" | "human";
const ACTOR_ICON = { family: Users, ai: ScanText, rules: ListChecks, human: Stethoscope } as const;

export type StoryStep = { key: string; actor: Actor; title: string; alt: string; altLang: string; body: string; actorLabel: string; srStep: string };

/**
 * How it works, as a story. Every step's text is always in the page. On a desktop with motion allowed
 * (html.motion-ok, ≥1024 px) the visuals sit on one sticky stage and the stage follows the step being read
 * (scroll-linked, crossfade only). Everywhere else (phones, reduced motion, Pause motion, no JavaScript) each
 * step shows its own visual inline: a plain list. The CSS in globals.css (.story-*) decides which.
 */
export function HowStory({ steps, visuals, num }: { steps: StoryStep[]; visuals: ReactNode[]; num: string[] }) {
  const list = useRef<HTMLOListElement>(null);
  const [active, setActive] = useState<number | null>(null);
  const { scrollYProgress } = useScroll({ target: list, offset: ["start 55%", "end 55%"] });
  useMotionValueEvent(scrollYProgress, "change", (v) => {
    setActive(Math.min(steps.length - 1, Math.max(0, Math.floor(v * steps.length))));
  });

  return (
    <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:gap-16">
      <div aria-hidden className="story-stage relative min-w-0 lg:sticky lg:top-28 lg:h-[480px] lg:self-start"
        data-active={active ?? undefined}>
        {visuals.map((v, i) => (
          <div key={i} className="story-layer" data-i={i} data-on={active === i ? "" : undefined}>{v}</div>
        ))}
      </div>
      <ol ref={list} className="relative min-w-0">
        <span aria-hidden className="stitch-y absolute bottom-8 left-[19px] top-8" />
        {steps.map((s, i) => {
          const Icon = ACTOR_ICON[s.actor];
          const human = s.actor === "human";
          return (
            <li key={s.key} className="story-step relative grid grid-cols-[40px_minmax(0,1fr)] gap-x-5 py-6 lg:min-h-[38vh]"
              data-on={active === i ? "" : undefined}>
              <span aria-hidden
                className={`story-num relative grid h-10 w-10 place-items-center rounded-full border-2 font-display text-lg tabular ${
                  human ? "border-neel bg-neel text-on-neel" : "border-stitch bg-paper-raised text-ink"}`}>
                {num[i]}
              </span>
              <div className="min-w-0 pt-1">
                <h3 className="flex flex-wrap items-baseline gap-x-2 text-[22px] font-semibold leading-snug text-ink">
                  <span className="sr-only">{s.srStep}: </span>
                  {s.title}
                  <span lang={s.altLang} className="text-[16px] font-medium text-ink-faint">{s.alt}</span>
                </h3>
                <p className="mt-1 max-w-[52ch] text-[17px] leading-relaxed text-ink-soft">{s.body}</p>
                <p className={`mt-2 inline-flex items-center gap-1.5 text-[14px] font-semibold ${human ? "text-neel" : "text-ink-faint"}`}>
                  <Icon aria-hidden size={15} /> {s.actorLabel}
                </p>
                <div aria-hidden className="story-inline mt-5 max-w-[440px]">{visuals[i]}</div>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
