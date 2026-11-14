"use client";

import { History } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { date, num } from "@/lib/format";
import { useApi } from "@/lib/useApi";

/** What happened in this household, so siblings abroad stop phoning each other to ask. */
export function FamilyActivity({ pid }: { pid: number }) {
  const t = useTranslations("activity");
  const locale = useLocale();
  const log = useApi(() => api.activity(pid), [pid], 60000);
  if (!log.data?.length) return null;
  return (
    <section aria-labelledby="activity-h" className="rounded-card border border-rule bg-paper-raised p-5">
      <h2 id="activity-h" className="flex items-center gap-2 font-semibold"><History aria-hidden size={20} className="text-neel" /> {t("title")}</h2>
      <ol className="mt-3 grid gap-2.5">
        {log.data.slice(0, 6).map((a, i) => (
          <li key={i} className="flex items-baseline justify-between gap-3 border-b border-rule pb-2 last:border-b-0 last:pb-0">
            <span className="min-w-0 text-ink">{t(`kind.${a.kind}`, { n: num(a.n ?? 1, locale), count: a.n ?? 1 })}</span>
            <span className="shrink-0 text-[15px] text-ink-faint">{date(a.created_at, locale, { day: "numeric", month: "short" })}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
