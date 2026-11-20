"use client";

import { Check, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { DemoTag } from "@/components/Chrome";
import { DuplicateConnector } from "@/components/DuplicateConnector";
import { StripCard } from "@/components/StripCard";
import { DEMO_ITEMS } from "@/lib/demoData";
import { motionAllowed } from "@/lib/motionPref";

/** When frames 1-4 start (ms). Frame 4 is the finished state the server renders. */
const STEPS = [300, 900, 1400, 1700] as const;
const SEEN = "heroSeen";

/**
 * The family's shelf, finished: Napa and Ace bracketed as the same medicine, Camlodin on its own, and a
 * pharmacist's confirmation. The server renders this final frame. Only when motion is allowed (html.motion-ok)
 * and the visitor has not seen it this session (html.hero-seen) do the start-state rules in globals.css
 * apply, so the moment plays once, data-step 0 to 4: Ace slides up to Napa, the bracket draws, the label
 * turns red, the pharmacist confirms. Every change is a transform or a colour; no text is ever hidden.
 * Real components, invented household. Its Bangla strings come from ProductFrames (server), which passes
 * only the two namespaces the cards use instead of the whole messages file.
 */
export function HeroDemo({ replayLabel }: { replayLabel: string }) {
  // Rendered as step 0, but the start state only exists under html.motion-ok (set before paint) and not
  // html.hero-seen; everyone else sees the finished frame from the first paint.
  const [step, setStep] = useState(0);
  const [replay, setReplay] = useState(0);
  const timers = useRef<number[]>([]);

  useEffect(() => {
    const clear = () => timers.current.forEach(clearTimeout);
    clear();
    const html = document.documentElement;
    const play = motionAllowed() && (replay > 0 || !html.classList.contains("hero-seen"));
    if (!play) {
      setStep(4);
      return;
    }
    setStep(0);
    timers.current = STEPS.map((ms, i) => window.setTimeout(() => setStep(i + 1), ms));
    timers.current.push(window.setTimeout(() => {
      try { sessionStorage.setItem(SEEN, "1"); } catch {}
      html.classList.add("hero-seen");
    }, STEPS[3] + 700));
    return clear;
  }, [replay]);

  return (
    <div lang="bn" className="hero-demo relative mx-auto w-full min-w-0 max-w-[440px]" data-step={step}
      data-replay={replay > 0 ? "" : undefined}>
      <div className="rounded-[20px] border border-rule-strong bg-paper p-4 shadow-lift sm:p-5">
        <div className="mb-4 flex items-center justify-between gap-2">
          <p className="font-bn-display text-[22px] leading-none text-ink">রহিমা বেগমের তাক</p>
          <button
            type="button"
            onClick={() => setReplay((r) => r + 1)}
            aria-label={replayLabel}
            title={replayLabel}
            className="hero-replay inline-flex h-12 w-12 items-center justify-center rounded-full border border-rule text-ink-soft hover:text-ink"
          >
            <RotateCcw aria-hidden size={17} />
          </button>
        </div>
        <div className="grid gap-3 text-[18px]">
          <DuplicateConnector label="দুটোই প্যারাসিটামল" animate={false} className="hero-pair">
            <StripCard item={DEMO_ITEMS.napa} density="compact" titleAs="p" highlight="red" />
            <div className="hero-ace"><StripCard item={DEMO_ITEMS.ace} density="compact" titleAs="p" highlight="red" /></div>
          </DuplicateConnector>
          <StripCard item={DEMO_ITEMS.camlodin} density="compact" titleAs="p" />
        </div>
        <p className="hero-status mt-4 flex min-h-8 items-center text-[16px] font-semibold">
          <span className="hero-done inline-flex items-center gap-2 text-green">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-green text-paper-raised">
              <Check aria-hidden size={15} strokeWidth={3} />
            </span>
            ফার্মাসিস্ট নিশ্চিত করেছেন
          </span>
          <span aria-hidden className="hero-wait items-center gap-2 text-ink-soft">
            <span className="h-2.5 w-2.5 rounded-full bg-amber" /> ফার্মাসিস্টের অপেক্ষায়
          </span>
        </p>
      </div>
      <DemoTag className="mt-4 border-solid border-paper bg-paper text-ink" />
    </div>
  );
}
