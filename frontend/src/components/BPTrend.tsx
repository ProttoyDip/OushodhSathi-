"use client";

import { useLocale, useTranslations } from "next-intl";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { date, num } from "@/lib/format";

type Reading = { taken_on: string; systolic: number; diastolic: number };

/** 7-day blood pressure with the 140/90 target drawn as labelled reference lines. */
export function BPTrend({
  readings,
  target = { systolic: 140, diastolic: 90 },
  height = 240,
}: {
  readings: Reading[];
  target?: { systolic: number; diastolic: number };
  height?: number;
}) {
  const locale = useLocale();
  const t = useTranslations("report");
  const data = readings.map((r) => ({ ...r, day: date(r.taken_on, locale, { weekday: "short" }) }));
  const tick = { fill: "var(--ink-faint)", fontSize: 13 };
  const latest = readings.at(-1);

  return (
    <figure className="m-0">
      <figcaption className="sr-only">
        {t("bpTitle")}.{" "}
        {readings.map((r) => `${date(r.taken_on, locale)}: ${r.systolic}/${r.diastolic}`).join("; ")}
      </figcaption>
      {latest && (
        <p className="mb-3 flex items-baseline gap-2">
          <span className="text-sm text-ink-faint">{t("bpLatest")}</span>
          <span className="tabular font-display text-[34px] leading-none text-ink">
            {num(latest.systolic, locale)}/{num(latest.diastolic, locale)}
          </span>
          <span className="text-sm text-ink-faint">mmHg</span>
        </p>
      )}
      <div style={{ height }} aria-hidden>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 52, bottom: 0, left: -18 }}>
            <CartesianGrid stroke="var(--rule)" strokeDasharray="2 4" vertical={false} />
            <XAxis dataKey="day" tick={{ ...tick, fontSize: 12 }} interval={0} tickLine={false} axisLine={{ stroke: "var(--rule-strong)" }} />
            <YAxis
              domain={[70, 180]}
              ticks={[80, 100, 120, 140, 160, 180]}
              tick={tick}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => num(v, locale)}
            />
            <ReferenceLine
              y={target.systolic}
              stroke="var(--red)"
              strokeDasharray="5 4"
              strokeWidth={1.5}
              label={{ value: num(target.systolic, locale), position: "right", fill: "var(--red)", fontSize: 13, fontWeight: 600 }}
            />
            <ReferenceLine
              y={target.diastolic}
              stroke="var(--red)"
              strokeDasharray="5 4"
              strokeWidth={1.5}
              label={{ value: num(target.diastolic, locale), position: "right", fill: "var(--red)", fontSize: 13, fontWeight: 600 }}
            />
            <Tooltip
              contentStyle={{
                background: "var(--paper-raised)",
                border: "1px solid var(--rule)",
                borderRadius: 8,
                color: "var(--ink)",
                fontSize: 14,
              }}
              labelStyle={{ color: "var(--ink-soft)" }}
              formatter={(v, name) => [num(Number(v), locale), name === "systolic" ? t("systolic") : t("diastolic")]}
            />
            <Line type="monotone" dataKey="systolic" stroke="var(--ink)" strokeWidth={2.5} dot={{ r: 3.5, fill: "var(--ink)" }} isAnimationActive={false} />
            <Line type="monotone" dataKey="diastolic" stroke="var(--teal)" strokeWidth={2.5} dot={{ r: 3.5, fill: "var(--teal)" }} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-ink-soft">
        <span className="inline-flex items-center gap-1.5"><i className="block h-0.5 w-5 bg-ink" />{t("systolic")}</span>
        <span className="inline-flex items-center gap-1.5"><i className="block h-0.5 w-5 bg-teal" />{t("diastolic")}</span>
        <span className="inline-flex items-center gap-1.5 text-red">
          <i className="block h-0 w-5 border-t-[1.5px] border-dashed border-red" />
          {t("bpTarget")}
        </span>
      </div>
    </figure>
  );
}
