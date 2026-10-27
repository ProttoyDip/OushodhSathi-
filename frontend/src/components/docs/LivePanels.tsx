"use client";

import { CircleCheck, CircleDashed, CircleX, Cpu } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { api } from "@/lib/api";
import { cx } from "@/lib/format";
import { useApi } from "@/lib/useApi";

const code = (chunks: ReactNode) => <code className="font-mono text-[14px]">{chunks}</code>;

function Dot({ ok, idle }: { ok: boolean; idle?: boolean }) {
  const Icon = idle ? CircleDashed : ok ? CircleCheck : CircleX;
  return <Icon aria-hidden size={17} className={cx("shrink-0", idle ? "text-ink-faint" : ok ? "text-green" : "text-red")} />;
}

export function LiveStatus() {
  const t = useTranslations("docs.live");
  const tm = useTranslations("models");
  const health = useApi(() => api.health(), [], 30000);
  const h = health.data;
  if (health.error)
    return (
      <p className="rounded-card border border-red-line bg-red-tint p-4 text-red">
        {t("unreachable", { reason: health.error.status === 0 ? t("offline") : `HTTP ${health.error.status}` })}
      </p>
    );
  if (!h) return <div className="h-48 rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />;
  const web = [h.web_lookup.tavily && "Tavily", h.web_lookup.perplexity && "Perplexity"].filter(Boolean).join(" + ");
  const rows: [string, ReactNode, boolean, boolean?][] = [
    [t("api"), h.status, h.status === "ok"],
    [t("mode"), h.demo_mode ? t("modeDemo") : t("modeLive"), true],
    [t("vision"), h.providers.vision.join(" → ") || t("noneConfigured"), h.providers.vision.length > 0, h.providers.vision.length === 0],
    [t("text"), h.providers.text.join(" → ") || t("noneConfigured"), h.providers.text.length > 0, h.providers.text.length === 0],
    [t("explain"), h.providers.explain_bn.join(" → ") || t("templates"), true],
    [t("visionModel"), h.models.vision, true],
    [t("textModel"), h.models.text, true],
    [t("local"), h.models.explain_bn_local ? `${h.models.explain_bn_local} · ${h.ollama_reachable ? t("reachable") : t("notReachable")}` : t("notSet"), h.ollama_reachable, !h.ollama_reachable],
    [t("web"), web || t("notConfigured"), !!web, !web],
    [t("prompts"), Object.values(h.prompts).join(", "), true],
    [t("reviewer"), h.reviewer_login, h.reviewer_login !== "missing"],
    [t("tests"), String(h.test_count), true],
  ];
  return (
    <div>
      <table className="w-full border-collapse text-left text-[15px]">
        <tbody>
          {rows.map(([k, v, ok, idle]) => (
            <tr key={k} className="border-b border-rule">
              <th scope="row" className="w-[42%] py-2.5 pr-4 font-medium text-ink-soft">{k}</th>
              <td className="py-2.5">
                <span className="flex items-center gap-2 text-ink"><Dot ok={ok} idle={idle} /><span className="tabular break-all">{v}</span></span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-3 text-[13px] text-ink-faint">{t("footnote")}</p>
      <Link href="/models?from=/docs" className="mt-3 inline-flex h-11 items-center gap-2 rounded-chip border border-rule px-4 text-[15px] font-medium text-ink hover:border-rule-strong">
        <Cpu aria-hidden size={16} /> {tm("title")}
      </Link>
    </div>
  );
}

const pct = (x: number) => `${(x * 100).toFixed(1)}%`;

function Ci({ ci, label }: { ci?: [number, number]; label: string }) {
  if (!ci) return null;
  return <span className="block text-[13px] text-ink-faint">{label} {pct(ci[0])}–{pct(ci[1])}</span>;
}

export function PilotPanel() {
  const t = useTranslations("docs.live");
  const stats = useApi(() => api.pilotStats(), []);
  if (stats.error || !stats.data)
    return <div className="h-24 rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />;
  const s = stats.data;
  if (s.households === 0)
    return (
      <div className="rounded-card border border-dashed border-rule-strong p-5">
        <p className="!mt-0 text-lg font-semibold text-ink">{t("noPilotTitle")}</p>
        <p className="mt-1 text-ink-soft">{t.rich("noPilotBody", { code })}</p>
      </div>
    );
  return (
    <div>
      <table className="w-full border-collapse text-left text-[15px]">
        <thead className="text-ink-faint">
          <tr className="border-b border-rule-strong">
            <th className="py-2 font-medium">{t("measure")}</th><th className="font-medium">{t("count")}</th>
            <th className="font-medium">{t("proportion")}</th><th className="font-medium">{t("wilson")}</th>
          </tr>
        </thead>
        <tbody className="tabular">
          {s.proportions.map((p) => (
            <tr key={p.label} className="border-b border-rule">
              <td className="py-2.5 pr-4 font-medium">{p.label}</td>
              <td>{p.k} / {p.n}</td>
              <td>{pct(p.p)}</td>
              <td className="text-ink-soft">{pct(p.ci_low)}–{pct(p.ci_high)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-3 text-[13px] text-ink-faint">{t("pilotFoot", { households: s.households, medicines: s.medicines ?? 0 })}</p>
    </div>
  );
}

export function EvalPanel() {
  const t = useTranslations("docs.live");
  const results = useApi(() => api.evalResults(), []);
  if (results.error || !results.data)
    return <div className="h-24 rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />;
  if (results.data.length === 0)
    return (
      <div className="rounded-card border border-dashed border-rule-strong p-5">
        <p className="!mt-0 text-lg font-semibold text-ink">{t("evalTitle")}</p>
        <p className="mt-1 text-ink-soft">{t.rich("evalBody", { code })}</p>
      </div>
    );
  return (
    <table className="w-full border-collapse text-left text-[15px]">
      <thead className="text-ink-faint">
        <tr className="border-b border-rule-strong">
          <th className="py-2 font-medium">{t("prompt")}</th><th className="font-medium">{t("model")}</th><th className="font-medium">{t("photos")}</th>
          <th className="font-medium">{t("brand")}</th><th className="font-medium">{t("strength")}</th><th className="font-medium">{t("conf")}</th>
        </tr>
      </thead>
      <tbody className="tabular">
        {results.data.map((r) => (
          <tr key={r.prompt_version + r.run_at} className="border-b border-rule">
            <td className="py-2.5 font-medium">{r.prompt_version}</td>
            <td className="break-all text-ink-soft">{r.model_id ?? "—"}</td>
            <td>{r.images} / {r.labelled_items}</td>
            <td>{pct(r.brand_accuracy)}<Ci ci={r.brand_accuracy_ci} label={t("ci")} /></td>
            <td>{pct(r.strength_accuracy)}<Ci ci={r.strength_accuracy_ci} label={t("ci")} /></td>
            <td>{r.avg_confidence ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Sathi's safety eval: the real numbers from eval/sathi_results_*.json. */
export function SathiEvalPanel() {
  const t = useTranslations("docs.live");
  const runs = useApi(() => api.sathiEval(), []);
  const r = runs.data?.[runs.data.length - 1];
  if (!r) return <div className="h-24 rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />;
  return (
    <div>
      <table className="w-full border-collapse text-left text-[15px]">
        <thead className="text-ink-faint">
          <tr className="border-b border-rule-strong">
            <th className="py-2 font-medium">{t("sathiCategory")}</th><th className="font-medium">{t("sathiResult")}</th><th className="font-medium">{t("sathiTarget")}</th>
          </tr>
        </thead>
        <tbody className="tabular">
          {Object.entries(r.by_category).map(([cat, s]) => (
            <tr key={cat} className="border-b border-rule">
              <td className="py-2.5 font-medium">{t(`sathiCat.${cat}`)}</td>
              <td>{s.correct} / {s.n} · <b className={s.rate >= s.target ? "text-green" : "text-red"}>{pct(s.rate)}</b></td>
              <td className="text-ink-soft">{pct(s.target)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-[13px] text-ink-faint">{t("sathiMeta", { cases: r.cases, mode: r.mode, version: r.prompt_version, leaks: r.leaks.length })}</p>
    </div>
  );
}

/** Median minutes from opening a finding to deciding it: the cost of a pharmacist review. */
export function ReviewTimePanel() {
  const t = useTranslations("docs.live");
  const rt = useApi(() => api.reviewTime(), []);
  if (!rt.data) return <div className="h-16 rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />;
  const { reviews, median_seconds } = rt.data;
  return (
    <div className="rounded-card border border-rule bg-paper-raised p-5">
      <p className="!mt-0 tabular font-display text-[34px] leading-none text-ink">
        {median_seconds == null ? "—" : median_seconds < 90 ? t("seconds", { n: Math.round(median_seconds) }) : t("minutes", { n: (median_seconds / 60).toFixed(1) })}
      </p>
      <p className="mt-1 text-ink-soft">{reviews ? t("reviewTimeBody", { n: reviews }) : t("reviewTimeNone")}</p>
    </div>
  );
}
