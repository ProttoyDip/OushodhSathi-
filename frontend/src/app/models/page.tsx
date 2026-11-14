"use client";

import { CircleCheck, Cpu, Languages, Lock, MessageCircleHeart, ScanText, Search, ShieldCheck } from "lucide-react";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { FamilyHeader, familyWidth } from "@/components/Chrome";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { cx } from "@/lib/format";
import { reviewerSession } from "@/lib/reviewer";
import type { ModelRef, ModelsInfo, ModelTask } from "@/lib/types";
import { useApi } from "@/lib/useApi";
import { reveal } from "@/lib/reveal";

// Provider names are proper nouns: shown as-is in both languages.
const PROVIDER: Record<string, string> = {
  nvidia: "NVIDIA",
  openrouter: "OpenRouter",
  nararouter: "NARAROUTER",
  explab: "Experimental Lab",
  agentrouter: "Agent Router",
  ollama: "Ollama",
};
const TASKS = [
  { key: "vision", Icon: ScanText },
  { key: "text", Icon: Search },
  { key: "explain_bn", Icon: Languages },
  { key: "sathi", Icon: MessageCircleHeart },
] as const;

const refKey = (r: ModelRef) => `${r.provider}|${r.model}`;
const same = (a: ModelRef | null | undefined, b: ModelRef) => !!a && a.provider === b.provider && a.model === b.model;

/** Back goes where the visitor came from; only a same-site path is accepted (no open redirect). */
function backTarget(from: string | null): string {
  return from && from.startsWith("/") && !from.startsWith("//") && !from.includes("\\") ? from : "/";
}

export default function ModelsPage() {
  return (
    <Suspense>
      <Models />
    </Suspense>
  );
}

/** Which AI models the app uses, in which order, what answered last — and the user's choice. */
function Models() {
  const t = useTranslations("models");
  const back = backTarget(useSearchParams().get("from"));
  const info = useApi(() => api.models(), [], 30000);
  // choosing a model changes it for every family, so only a signed-in reviewer may
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => setToken(reviewerSession()?.token ?? null), []);

  return (
    <>
      <FamilyHeader back={back} />
      <main className={`mx-auto w-full px-4 pb-16 pt-4 lg:pt-8 ${familyWidth}`}>
        <h1 className="font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t("title")}</h1>
        <p className="mt-2 max-w-[70ch] text-ink-soft">{t("intro")}</p>
        <p className="mt-3 flex max-w-[70ch] items-start gap-2 text-base text-ink-soft">
          <ShieldCheck aria-hidden size={20} className="mt-0.5 shrink-0 text-neel" />
          {t("safety")}
        </p>

        {info.error ? (
          <div className="mt-6"><ErrorState error={info.error} onRetry={info.reload} /></div>
        ) : !info.data ? (
          <>
            <p className="mt-6 text-base text-ink-faint" aria-live="polite">{t("checking")}</p>
            <Skeleton lines={4} className="mt-3 lg:grid-cols-2 xl:grid-cols-4" />
          </>
        ) : (
          <div className="mt-8 grid grid-cols-[minmax(0,1fr)] gap-5 lg:grid-cols-2 lg:items-start xl:grid-cols-4">
            {TASKS.map(({ key, Icon }, i) => (
              <TaskCard key={key} index={i} kind={key} Icon={Icon} task={info.data!.tasks[key]} token={token} onChange={(d) => info.setData(d)} />
            ))}
          </div>
        )}
      </main>
    </>
  );
}

function TaskCard({ index, kind, Icon, task, token, onChange }: {
  index: number;
  kind: "vision" | "text" | "explain_bn" | "sathi";
  Icon: typeof ScanText;
  task: ModelTask;
  token: string | null;
  onChange: (d: ModelsInfo) => void;
}) {
  const t = useTranslations("models");
  const [state, setState] = useState<"idle" | "saving" | "saved" | "failed">("idle");

  async function choose(value: string) {
    if (kind === "explain_bn" || kind === "sathi" || !token) return;
    setState("saving");
    try {
      const [provider, ...rest] = value.split("|");
      onChange(await api.setModel(token, kind, value === "auto" ? null : { provider, model: rest.join("|") }));
      setState("saved");
    } catch {
      setState("failed");
    }
  }

  return (
    <section {...reveal(index * 90)} aria-labelledby={`task-${kind}`} className="rounded-card border border-rule bg-paper-raised p-5 shadow-soft">
      <div className="flex items-center gap-3">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-neel-tint text-neel">
          <Icon aria-hidden size={22} />
        </span>
        <h2 id={`task-${kind}`} className="text-xl font-semibold text-ink">{t(`task.${kind}.title`)}</h2>
      </div>
      <p className="mt-3 text-base text-ink-soft">{t(`task.${kind}.desc`)}</p>

      {task.chain.length === 0 ? (
        <p className="mt-4 rounded-card border border-dashed border-rule-strong p-4 text-base text-ink-soft">{t("none")}</p>
      ) : (
        <ol className="mt-4 grid gap-2">
          {task.chain.map((m, i) => {
            const answered = same(task.last_used, m);
            return (
              <li
                key={refKey(m)}
                className={cx(
                  "grid grid-cols-[auto_minmax(0,1fr)] items-start gap-x-3 rounded-md border px-3 py-2.5",
                  i === 0 ? "border-neel bg-neel-tint/60" : "border-rule",
                )}
              >
                <span className="tabular mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-paper-sunk text-[13px] font-semibold text-ink-soft">
                  {i + 1}
                </span>
                <span className="min-w-0">
                  <span className="block break-words text-[15px] font-semibold leading-snug text-ink">{m.model}</span>
                  <span className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[13px] text-ink-soft">
                    <span className="inline-flex items-center gap-1">
                      <Cpu aria-hidden size={13} />
                      {PROVIDER[m.provider] ?? m.provider}
                      {m.provider === "ollama" && ` · ${t("local")}`}
                    </span>
                    <span className="text-ink-faint">{i === 0 ? t("first") : t("backup", { n: i })}</span>
                    {same(task.preferred, m) && (
                      <span className="rounded-chip bg-neel px-2 py-0.5 font-semibold text-on-neel">{t("yourChoice")}</span>
                    )}
                    {answered && <CircleCheck aria-label={t("lastUsed", { model: m.model })} size={14} className="text-green" />}
                  </span>
                </span>
              </li>
            );
          })}
        </ol>
      )}

      <p className="mt-3 text-[13px] text-ink-faint">
        {task.last_used
          ? `${t("lastUsed", { model: task.last_used.model })} ${task.last_used.cached ? t("lastCached") : ""}`
          : t("never")}
      </p>

      {task.choosable && task.chain.length > 0 && !token ? (
        <p className="mt-4 flex items-start gap-2 border-t border-rule pt-4 text-[13px] text-ink-soft">
          <Lock aria-hidden size={14} className="mt-0.5 shrink-0" />
          {t("chooseReviewerOnly")}
        </p>
      ) : task.choosable && task.chain.length > 0 ? (
        <div className="mt-4 border-t border-rule pt-4">
          <label htmlFor={`choose-${kind}`} className="text-base font-semibold text-ink">{t("choose")}</label>
          <select
            id={`choose-${kind}`}
            value={task.preferred ? refKey(task.preferred) : "auto"}
            onChange={(e) => choose(e.target.value)}
            disabled={state === "saving"}
            className="mt-1.5 block h-12 w-full rounded-md border border-rule-strong bg-paper px-3 text-base text-ink disabled:opacity-60"
          >
            <option value="auto">{t("auto")}</option>
            {task.chain.map((m) => (
              <option key={refKey(m)} value={refKey(m)}>
                {m.model} — {PROVIDER[m.provider] ?? m.provider}
              </option>
            ))}
          </select>
          <p className={cx("mt-2 min-h-5 text-[13px]", state === "failed" ? "text-red" : "text-ink-soft")} aria-live="polite">
            {state === "saved" ? t("saved") : state === "failed" ? t("failed") : ""}
          </p>
        </div>
      ) : kind === "explain_bn" || kind === "sathi" ? (
        <p className="mt-4 border-t border-rule pt-4 text-[13px] text-ink-soft">{t("fixedNote")} {t("templates")}</p>
      ) : null}
    </section>
  );
}
