"use client";

import { LoaderCircle } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

/**
 * Shown while the hosted API wakes from sleep (lib/api.ts wakeServer). The page keeps waiting and retries by
 * itself; this only tells the visitor why it is slow, so nobody gives up on a working site.
 */
export function ServerWaking() {
  const t = useTranslations("common");
  const [show, setShow] = useState(false);
  useEffect(() => {
    const on = () => setShow(true);
    const off = () => setShow(false);
    window.addEventListener("api:waking", on);
    window.addEventListener("api:awake", off);
    return () => {
      window.removeEventListener("api:waking", on);
      window.removeEventListener("api:awake", off);
    };
  }, []);
  return (
    <div aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center px-4">
      {show && (
        <p className="pointer-events-auto flex max-w-[560px] items-start gap-3 rounded-card border border-rule-strong bg-paper-raised px-5 py-4 text-[16px] leading-relaxed text-ink shadow-lift">
          <LoaderCircle aria-hidden size={20} className="mt-0.5 shrink-0 animate-spin text-neel motion-reduce:animate-none" />
          <span>
            <strong className="block font-semibold">{t("waking")}</strong>
            <span className="text-ink-soft">{t("wakingBody")}</span>
          </span>
        </p>
      )}
    </div>
  );
}
