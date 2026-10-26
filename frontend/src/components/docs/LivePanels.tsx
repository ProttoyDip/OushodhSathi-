"use client";

import { CircleCheck, CircleDashed, CircleX } from "lucide-react";
import { api } from "@/lib/api";
import { cx } from "@/lib/format";
import { useApi } from "@/lib/useApi";

function Dot({ ok, idle }: { ok: boolean; idle?: boolean }) {
  const Icon = idle ? CircleDashed : ok ? CircleCheck : CircleX;
  return <Icon aria-hidden size={17} className={cx("shrink-0", idle ? "text-ink-faint" : ok ? "text-green" : "text-red")} />;
}

export function LiveStatus() {
  const health = useApi(() => api.health(), [], 30000);
  const h = health.data;
  if (health.error)
    return (
      <p className="rounded-card border border-red-line bg-red-tint p-4 text-red">
        The API is not reachable from this page right now ({health.error.status === 0 ? "offline" : `HTTP ${health.error.status}`}).
      </p>
    );
  if (!h) return <div className="h-48 rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />;
  const rows: [string, React.ReactNode, boolean, boolean?][] = [
    ["API", h.status, h.status === "ok"],
    ["Mode", h.demo_mode ? "Demo mode (works without keys)" : "Live", true],
    ["Vision providers", h.providers.vision.join(" → ") || "none configured", h.providers.vision.length > 0, h.providers.vision.length === 0],
    ["Text providers", h.providers.text.join(" → ") || "none configured", h.providers.text.length > 0, h.providers.text.length === 0],
    ["Bangla explanations", h.providers.explain_bn.join(" → ") || "fixed templates", true],
    ["Vision model", h.models.vision, true],
    ["Text model", h.models.text, true],
    ["Local model (Ollama)", h.models.explain_bn_local ? `${h.models.explain_bn_local} · ${h.ollama_reachable ? "reachable" : "not reachable"}` : "not set", h.ollama_reachable, !h.ollama_reachable],
    ["Web lookup", [h.web_lookup.tavily && "Tavily", h.web_lookup.perplexity && "Perplexity"].filter(Boolean).join(" + ") || "not configured", h.web_lookup.tavily || h.web_lookup.perplexity, !(h.web_lookup.tavily || h.web_lookup.perplexity)],
    ["Prompts in use", Object.values(h.prompts).join(", "), true],
    ["Reviewer login", h.reviewer_login, h.reviewer_login !== "missing"],
    ["Test functions", String(h.test_count), true],
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
      <p className="mt-3 text-[13px] text-ink-faint">Read live from GET /health every 30 seconds. Provider names only; keys never leave the server.</p>
    </div>
  );
}

export function EvalPanel() {
  const results = useApi(() => api.evalResults(), []);
  if (results.error || !results.data)
    return <div className="h-24 rounded-card bg-paper-sunk" style={{ animation: "breathe 1.6s ease-in-out infinite" }} />;
  if (results.data.length === 0)
    return (
      <div className="rounded-card border border-dashed border-rule-strong p-5">
        <p className="text-lg font-semibold text-ink">Evaluation in progress.</p>
        <p className="mt-1 text-ink-soft">
          No labelled real-photo results have been recorded yet. When <code className="font-mono text-[14px]">eval/run_eval.py</code> runs
          on our photo set it writes <code className="font-mono text-[14px]">eval/results_&lt;prompt&gt;.json</code>, and the numbers appear here automatically.
        </p>
      </div>
    );
  return (
    <table className="w-full border-collapse text-left text-[15px]">
      <thead className="text-ink-faint">
        <tr className="border-b border-rule-strong">
          <th className="py-2 font-medium">Prompt</th><th className="font-medium">Model</th><th className="font-medium">Photos / items</th>
          <th className="font-medium">Brand</th><th className="font-medium">Strength</th><th className="font-medium">Avg conf.</th>
        </tr>
      </thead>
      <tbody className="tabular">
        {results.data.map((r) => (
          <tr key={r.prompt_version + r.run_at} className="border-b border-rule">
            <td className="py-2.5 font-medium">{r.prompt_version}</td>
            <td className="break-all text-ink-soft">{r.model_id ?? "—"}</td>
            <td>{r.images} / {r.labelled_items}</td>
            <td>{(r.brand_accuracy * 100).toFixed(1)}%</td>
            <td>{(r.strength_accuracy * 100).toFixed(1)}%</td>
            <td>{r.avg_confidence ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
