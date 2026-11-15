"use client";

import { useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";

/** "Why?": the knowledge-graph path behind a finding (brand → generic → class → group or rule),
 * each step with the table it came from. It explains; the rules engine made the finding. Reviewer only. */
export function WhyPath({ token, flagId }: { token: string; flagId: number }) {
  const t = useTranslations("review.why");
  const w = useApi(() => api.flagWhy(token, flagId), [token, flagId]);
  const paths = w.data?.paths ?? [];
  return (
    <>
      <h3 className="font-semibold text-ink-soft">{t("title")}</h3>
      {paths.length === 0 ? (
        <p className="text-ink-faint">{w.data || w.error ? t("empty") : t("loading")}</p>
      ) : (
        <div>
          <ol className="grid gap-2" lang="en">
            {paths.map((steps, i) => (
              <li key={i} className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-ink">
                {steps.map((s, j) => (
                  <span key={j} className="inline-flex items-center gap-1.5">
                    {j > 0 && <span aria-hidden className="text-ink-faint">→</span>}
                    <span title={s.source ? `${s.via} · ${s.source}` : s.type}
                      className="rounded-full border border-rule px-2 py-0.5 text-[13px]">
                      {s.node}
                    </span>
                  </span>
                ))}
              </li>
            ))}
          </ol>
          <p className="mt-2 text-[13px] text-ink-faint">{t("caveat")}</p>
        </div>
      )}
    </>
  );
}
