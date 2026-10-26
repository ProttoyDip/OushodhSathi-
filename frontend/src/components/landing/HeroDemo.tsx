"use client";

import { RotateCcw } from "lucide-react";
import { NextIntlClientProvider } from "next-intl";
import { useEffect, useState } from "react";
import bn from "../../../messages/bn.json";
import { DemoTag } from "@/components/Chrome";
import { DuplicateConnector } from "@/components/DuplicateConnector";
import { StripCard } from "@/components/StripCard";
import { DEMO_ITEMS } from "@/lib/demoData";

const comet = { ...DEMO_ITEMS.camlodin, id: 9, brand: "Comet", strength: "500 mg", generic: "metformin", drug_class: "biguanide", expiry: "2027-05" };

/**
 * The family's phone, live: the shelf assembles card by card, then Napa and Ace
 * snap together under "দুটোই প্যারাসিটামল". Real components, invented household.
 */
export function HeroDemo() {
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
        <div className="rounded-[20px] border border-rule-strong bg-paper p-4 shadow-soft sm:p-5">
          <div className="mb-4 flex items-center justify-between gap-2">
            <p className="font-bn-display text-[22px] leading-none text-ink">রহিমা বেগমের তাক</p>
            <button
              type="button"
              onClick={() => setRun((r) => r + 1)}
              aria-label="Replay the demo animation"
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-rule text-ink-soft hover:text-ink"
            >
              <RotateCcw aria-hidden size={17} />
            </button>
          </div>
          <div key={run} className="grid gap-3 text-[18px]">
            {phase === 0 ? (
              [DEMO_ITEMS.napa, DEMO_ITEMS.camlodin, DEMO_ITEMS.ace, comet].map((it, i) => (
                <div key={it.id} style={{ animation: `assemble 260ms var(--ease-out-quint) ${i * 160}ms both` }}>
                  <StripCard item={it} density="compact" />
                </div>
              ))
            ) : (
              <>
                <DuplicateConnector label="দুটোই প্যারাসিটামল">
                  <StripCard item={DEMO_ITEMS.napa} density="compact" highlight="red" />
                  <StripCard item={DEMO_ITEMS.ace} density="compact" highlight="red" />
                </DuplicateConnector>
                <div style={{ animation: "settle 240ms var(--ease-out-quint) 120ms both" }}>
                  <StripCard item={DEMO_ITEMS.camlodin} density="compact" />
                </div>
              </>
            )}
          </div>
        </div>
        <DemoTag className="mt-3" />
      </div>
    </NextIntlClientProvider>
  );
}
