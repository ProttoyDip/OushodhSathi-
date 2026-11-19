"use client";

import { FlaskConical } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { api } from "@/lib/api";
import type { Proportion } from "@/lib/types";
import { useApi } from "@/lib/useApi";
import { GITHUB_URL } from "@/lib/site";

const pct = (p: Proportion | null | undefined) =>
  p ? `${Math.round(p.p * 100)}% (${p.k}/${p.n} · 95% CI ${Math.round(p.ci_low * 100)}–${Math.round(p.ci_high * 100)}%)` : "—";
const rate = (x: number | null | undefined) => (x == null ? "—" : `${Math.round(x * 100)}%`);

/** The synthetic benchmark, in its own card below the real-photo results and always labelled as
 * synthetic. Shows nothing at all until eval/run_synthetic.* has written its results files. */
export function SyntheticPanel() {
  const t = useTranslations("docs.live.synthetic");
  const locale = useLocale() as "bn" | "en";
  const s = useApi(() => api.syntheticEval(), []);
  const d = s.data;
  if (!d || (!d.strip && !d.bp)) return null;
  const strip = d.strip;
  return (
    <section aria-labelledby="synthetic-h" className="rounded-card border-2 border-dashed border-amber-line bg-amber-tint/40 p-5">
      <h3 id="synthetic-h" className="!mt-0 flex items-center gap-2 text-lg font-semibold text-ink">
        <FlaskConical aria-hidden size={20} className="text-amber" /> {t("title")}
      </h3>
      <p className="mt-1 font-semibold text-amber">{d.label[locale]}</p>
      <p className="mt-1 text-[15px] text-ink-soft">{t("body")}</p>

      {strip && (
        <>
          <p className="mt-4 font-semibold text-ink">{t("strip", { n: strip.n_photos ?? 0, items: strip.labelled_items ?? 0 })}</p>
          <table className="mt-2 w-full border-collapse text-left text-[15px]">
            <tbody className="tabular">
              {(["brand", "strength", "expiry", "needs_check"] as const).map((k) => (
                <tr key={k} className="border-b border-rule"><td className="py-1.5 pr-3 text-ink-soft">{t(`m.${k}`)}</td><td>{pct(strip[k])}</td></tr>
              ))}
              <tr className="border-b border-rule"><td className="py-1.5 pr-3 text-ink-soft">{t("m.catch")}</td>
                <td>{strip.second_read.ran_on_items ? pct(strip.second_read.strength_catch) : t("notRun")}</td></tr>
            </tbody>
          </table>
          {Object.keys(strip.by_condition).length > 0 && (
            <>
              <p className="mt-4 font-semibold text-ink">{t("byCondition")}</p>
              <ul className="mt-1 grid gap-1 text-[15px] text-ink-soft sm:grid-cols-2">
                {Object.entries(strip.by_condition).map(([c, p]) => (
                  <li key={c}><span className="text-ink">{t(`c.${c}` as never)}</span>: {pct(p)}</li>
                ))}
              </ul>
            </>
          )}
        </>
      )}

      {d.bp && (
        <p className="mt-4 text-[15px] text-ink-soft">
          <span className="font-semibold text-ink">{t("bp", { n: d.bp.n_photos ?? 0 })}</span>{" "}
          {t("bpLine", { sys: rate(d.bp.systolic_accuracy), dia: rate(d.bp.diastolic_accuracy), wrong: d.bp.wrong_and_not_flagged ?? 0 })}
        </p>
      )}
      <p className="mt-4 text-[13px] text-ink-faint">
        <a href={`${GITHUB_URL}/blob/main/${d.readme}`} target="_blank" rel="noreferrer" className="underline">{t("howMade")}</a>
      </p>
    </section>
  );
}
