"use client";

import { ArrowRight, Check, Send, Wallet } from "lucide-react";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { api } from "@/lib/api";
import { genericName, num } from "@/lib/format";
import type { SavingsRow } from "@/lib/types";
import { useApi } from "@/lib/useApi";

/** Same medicine, lower price. Never switches a brand: the family can only ask the pharmacist. */
export function SavingsCard({ pid }: { pid: number }) {
  const t = useTranslations("savings");
  const locale = useLocale();
  const s = useApi(() => api.savings(pid), [pid]);
  const taka = (n: number, digits = 0) => `৳${num(n, locale, digits)}`;
  if (!s.data) return null;
  const d = s.data;

  return (
    <section aria-labelledby="savings-h" className="rounded-card border border-rule bg-paper-raised p-5">
      <h2 id="savings-h" className="flex items-center gap-2 font-semibold">
        <Wallet aria-hidden size={20} className="text-neel" /> {t("title")}
      </h2>
      {d.items.length === 0 ? (
        <p className="mt-2 text-ink-soft">{t("none")}</p>
      ) : (
        <>
          <p className="mt-3 flex flex-wrap items-baseline gap-x-2">
            <span className="tabular font-display text-[34px] leading-none text-neel">{taka(d.total_yearly_bdt)}</span>
            <span className="text-ink-soft">{t("perYear", { month: taka(d.total_monthly_bdt) })}</span>
          </p>
          <ul className="mt-4 grid gap-3">
            {d.items.map((r) => <Row key={r.item_id} pid={pid} r={r} taka={taka} />)}
          </ul>
        </>
      )}
      <p lang="bn" className="mt-4 rounded-md border-l-4 border-neel bg-neel-tint/60 px-4 py-3 font-medium text-ink">{d.notice_bn}</p>
      <p lang="en" className="mt-1 px-1 text-[15px] text-ink-soft">{d.notice_en}</p>
      <p className="mt-2 px-1 text-[13px] text-ink-faint">{t("priceNote")}</p>
    </section>
  );
}

function Row({ pid, r, taka }: { pid: number; r: SavingsRow; taka: (n: number, d?: number) => string }) {
  const t = useTranslations("savings");
  const locale = useLocale();
  const [state, setState] = useState<"idle" | "sending" | "sent" | "failed">("idle");
  const generic = genericName(r.generic, locale);
  return (
    <li className="rounded-md border border-rule p-4">
      <p className="flex flex-wrap items-center gap-x-2 gap-y-1 font-semibold">
        {r.brand} <ArrowRight aria-hidden size={16} className="text-ink-faint" /> {r.alternative.brand}
        <span className="font-normal text-ink-soft">· {generic} {r.strength}</span>
      </p>
      <p className="tabular mt-1 text-[15px] text-ink-soft">
        {t("perTablet", { now: taka(r.current_mrp_bdt, 2), other: taka(r.alternative.mrp_bdt, 2) })}
        {" · "}<b className="font-semibold text-ink">{t("saves", { month: taka(r.monthly_bdt), year: taka(r.yearly_bdt) })}</b>
      </p>
      {state === "sent" ? (
        <p role="status" className="mt-3 flex items-center gap-1.5 text-[15px] font-medium text-green">
          <Check aria-hidden size={18} /> {t("sent")}{" "}
          <Link href={`/p/${pid}/questions`} className="text-neel underline underline-offset-4">{t("seeQuestions")}</Link>
        </p>
      ) : (
        <button
          type="button"
          disabled={state === "sending"}
          onClick={async () => {
            setState("sending");
            try {
              await api.askPharmacist(pid, t("question", { generic, alt: r.alternative.brand, brand: r.brand }));
              setState("sent");
            } catch {
              setState("failed");
            }
          }}
          className="press mt-3 inline-flex min-h-11 items-center gap-2 rounded-card border border-neel px-4 text-[15px] font-semibold text-neel hover:bg-neel-tint disabled:opacity-60"
        >
          <Send aria-hidden size={16} /> {t("ask")}
        </button>
      )}
      {state === "failed" && <p role="alert" className="mt-1 text-[15px] text-red">{t("failed")}</p>}
    </li>
  );
}
