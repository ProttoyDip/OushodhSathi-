"use client";

import { FlaskConical, Loader2, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { cx } from "@/lib/format";

/** A calm strip for judges on the demo household: jump between the views, or start over. */
export function JudgeBar({ pid = 1, className }: { pid?: number; className?: string }) {
  const t = useTranslations("judge");
  const [state, setState] = useState<"idle" | "busy" | "error">("idle");
  const links: [string, string][] = [
    [`/p/${pid}`, t("family")], ["/review", t("reviewer")], [`/passport/${pid}`, t("passport")], ["/docs", t("docs")],
  ];

  return (
    <div role="region" aria-label={t("label")} className={cx("no-print border-b border-dashed border-stitch bg-neel-tint/50", className)}>
      <div className="mx-auto flex max-w-[1180px] flex-wrap items-center gap-x-4 gap-y-1.5 px-4 py-2 text-sm lg:px-8">
        <span className="inline-flex items-center gap-1.5 font-semibold text-neel"><FlaskConical aria-hidden size={15} /> {t("label")}</span>
        <nav aria-label={t("label")} className="flex flex-wrap items-center gap-x-1">
          {links.map(([href, label], i) => (
            <span key={href} className="inline-flex items-center">
              {i > 0 && <span aria-hidden className="px-1 text-ink-faint">·</span>}
              <Link href={href} className="inline-flex min-h-11 min-w-11 items-center justify-center rounded px-1.5 font-medium text-ink underline-offset-4 hover:underline">{label}</Link>
            </span>
          ))}
        </nav>
        <button
          type="button"
          disabled={state === "busy"}
          onClick={async () => {
            setState("busy");
            try {
              await api.demoReset();
              window.location.reload();
            } catch {
              setState("error");
            }
          }}
          className="press ml-auto inline-flex min-h-11 items-center gap-1.5 rounded-md border border-neel/50 bg-paper-raised px-3 font-semibold text-neel hover:border-neel disabled:opacity-60"
        >
          {state === "busy" ? <Loader2 aria-hidden size={15} className="animate-spin motion-reduce:animate-none" /> : <RotateCcw aria-hidden size={15} />}
          {t("reset")}
        </button>
        {state === "error" && <span role="alert" className="text-red">{t("failed")}</span>}
      </div>
    </div>
  );
}

/** Wakes the free Render instance as soon as someone lands, so the demo is quick. */
export function WarmUp() {
  useEffect(() => {
    api.health().catch(() => {});
  }, []);
  return null;
}
