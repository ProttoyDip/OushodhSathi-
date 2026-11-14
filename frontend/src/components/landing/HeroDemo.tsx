"use client";

import { RotateCcw } from "lucide-react";
import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import { NextIntlClientProvider } from "next-intl";
import { useEffect, useState } from "react";
import bn from "../../../messages/bn.json";
import { DemoTag } from "@/components/Chrome";
import { DuplicateConnector } from "@/components/DuplicateConnector";
import { SPRING_TRAVEL } from "@/components/Motion";
import { StripCard } from "@/components/StripCard";
import { DEMO_ITEMS } from "@/lib/demoData";

const comet = { ...DEMO_ITEMS.camlodin, id: 9, brand: "Comet", strength: "500 mg", generic: "metformin", drug_class: "biguanide", expiry: "2027-05" };

/** A strip that keeps its identity across layouts, so it travels instead of popping. */
function Travel({ id, i = 0, enter = false, children }: { id: number; i?: number; enter?: boolean; children: React.ReactNode }) {
  return (
    <motion.div
      layoutId={`hero-${id}`}
      initial={enter ? { opacity: 0, y: 22, scale: 0.97 } : false}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.18 } }}
      transition={{ ...SPRING_TRAVEL, delay: i * 0.12 }}
    >
      {children}
    </motion.div>
  );
}

/**
 * The family's phone, live: the shelf assembles card by card, then Napa and Ace
 * travel together under "দুটোই প্যারাসিটামল". Real components, invented household.
 */
export function HeroDemo({ replayLabel }: { replayLabel: string }) {
  const [phase, setPhase] = useState<0 | 1>(0);
  const [run, setRun] = useState(0);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setPhase(1);
      return;
    }
    setPhase(0);
    const id = setTimeout(() => setPhase(1), 1500);
    return () => clearTimeout(id);
  }, [run]);

  return (
    <NextIntlClientProvider locale="bn" messages={bn} timeZone="Asia/Dhaka">
      <div lang="bn" className="relative mx-auto w-full min-w-0 max-w-[440px]">
        <div className="rounded-[20px] border border-rule-strong bg-paper p-4 shadow-lift sm:p-5">
          <div className="mb-4 flex items-center justify-between gap-2">
            <p className="font-bn-display text-[22px] leading-none text-ink">রহিমা বেগমের তাক</p>
            <button
              type="button"
              onClick={() => setRun((r) => r + 1)}
              aria-label={replayLabel}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-rule text-ink-soft hover:text-ink"
            >
              <RotateCcw aria-hidden size={17} />
            </button>
          </div>
          <LayoutGroup id={`hero-${run}`}>
            <div key={run} className="grid gap-3 text-[18px]">
              <AnimatePresence mode="popLayout" initial>
                {phase === 0 ? (
                  [DEMO_ITEMS.napa, DEMO_ITEMS.camlodin, DEMO_ITEMS.ace, comet].map((it, i) => (
                    <Travel key={it.id} id={it.id} i={i} enter>
                      <StripCard item={it} density="compact" />
                    </Travel>
                  ))
                ) : (
                  <motion.div key="pair" layout className="grid gap-3">
                    <DuplicateConnector label="দুটোই প্যারাসিটামল" snap={false} delay={250}>
                      <Travel id={DEMO_ITEMS.napa.id}><StripCard item={DEMO_ITEMS.napa} density="compact" highlight="red" /></Travel>
                      <Travel id={DEMO_ITEMS.ace.id}><StripCard item={DEMO_ITEMS.ace} density="compact" highlight="red" /></Travel>
                    </DuplicateConnector>
                    <Travel id={DEMO_ITEMS.camlodin.id}><StripCard item={DEMO_ITEMS.camlodin} density="compact" /></Travel>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </LayoutGroup>
        </div>
        <DemoTag className="mt-4 !border-white/35 !text-white/85" />
      </div>
    </NextIntlClientProvider>
  );
}
