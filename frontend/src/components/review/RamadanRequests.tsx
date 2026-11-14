"use client";

import { MoonStar, Sunset } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { api } from "@/lib/api";
import { cx, genericName, since } from "@/lib/format";
import type { RamadanRequest } from "@/lib/types";
import { useApi } from "@/lib/useApi";

type Slots = Record<number, ("sehri" | "iftar")[]>;

/** Fasting reviews the families asked for. The reviewer maps each medicine to sehri and/or
 * iftar and writes a note; nothing is pre-filled, because the plan is a clinical decision. */
export function RamadanRequests({ token, reviewer, now }: { token: string; reviewer: string; now: number }) {
  const t = useTranslations("review.ramadan");
  const reqs = useApi(() => api.ramadanRequests(token), [token], 60000);
  if (!reqs.data?.length) return null;
  return (
    <section aria-labelledby="ramadan-req-h" className="mb-8">
      <h2 id="ramadan-req-h" className="flex items-center gap-2 text-xl font-semibold text-ink">
        <MoonStar aria-hidden size={20} className="text-neel" /> {t("title", { n: reqs.data.length })}
      </h2>
      <p className="mt-1 max-w-[62ch] text-sm text-ink-soft">{t("intro")}</p>
      <ol className="mt-4 grid gap-4">
        {reqs.data.map((r) => <Plan key={r.patient.id} r={r} token={token} reviewer={reviewer} now={now} onDone={reqs.reload} />)}
      </ol>
    </section>
  );
}

function Plan({ r, token, reviewer, now, onDone }: { r: RamadanRequest; token: string; reviewer: string; now: number; onDone: () => void }) {
  const t = useTranslations("review.ramadan");
  const tp = useTranslations("passport");
  const locale = useLocale();
  const [slots, setSlots] = useState<Slots>({});
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const unplaced = r.items.filter((it) => !(slots[it.id]?.length)).length;
  const toggle = (id: number, slot: "sehri" | "iftar") =>
    setSlots((s) => ({ ...s, [id]: s[id]?.includes(slot) ? s[id].filter((x) => x !== slot) : [...(s[id] ?? []), slot] }));

  return (
    <li className="rounded-card border border-rule bg-paper-raised p-5">
      <p className="flex flex-wrap items-center gap-x-3 text-sm text-ink-soft">
        <b className="text-base font-semibold text-ink">{locale === "bn" ? r.patient.name_bn ?? r.patient.name : r.patient.name}, {r.patient.age}</b>
        <span>{t("asked", { time: since(r.requested_at, now) })}</span>
      </p>
      <table className="mt-3 w-full border-collapse text-sm">
        <thead className="text-left text-ink-faint">
          <tr className="border-b border-rule"><th className="py-2 font-medium">{t("medicine")}</th><th className="font-medium">{t("now")}</th>
            <th className="w-24 text-center font-medium"><MoonStar aria-hidden size={14} className="mr-1 inline" />{t("sehri")}</th>
            <th className="w-24 text-center font-medium"><Sunset aria-hidden size={14} className="mr-1 inline" />{t("iftar")}</th></tr>
        </thead>
        <tbody>
          {r.items.map((it) => (
            <tr key={it.id} className="border-b border-rule">
              <td className="py-2.5"><b className="font-semibold">{it.brand}</b> <span className="text-ink-soft">{it.generic ? genericName(it.generic, locale) : ""} {it.strength}</span></td>
              <td className="text-ink-soft">{it.schedule.length ? it.schedule.map((s) => tp(s)).join(" · ") : tp("asNeeded")}</td>
              {(["sehri", "iftar"] as const).map((slot) => (
                <td key={slot} className="text-center">
                  <input type="checkbox" aria-label={t("slotFor", { slot: t(slot), brand: it.brand })} checked={!!slots[it.id]?.includes(slot)}
                    onChange={() => toggle(it.id, slot)} className="h-5 w-5 accent-[var(--neel)]" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <label className="mt-4 block text-sm font-semibold text-ink">{t("note")}
        <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={3} maxLength={1000} placeholder={t("notePh")}
          className="mt-1 block w-full resize-y rounded-md border border-rule-strong bg-paper px-3 py-2 text-base font-normal text-ink" />
      </label>
      {unplaced > 0 && <p className="mt-2 text-[13px] text-amber">{t("unplaced", { n: unplaced })}</p>}
      {error && <p role="alert" className="mt-2 text-sm font-medium text-red">{t("failed")}</p>}
      <button type="button" disabled={busy || note.trim().length < 2}
        onClick={async () => {
          setBusy(true);
          setError(false);
          try {
            await api.ramadanApprove(token, r.patient.id, { reviewer, note: note.trim(),
              items: r.items.map((it) => ({ item_id: it.id, slots: slots[it.id] ?? [] })) });
            onDone();
          } catch {
            setError(true);
          } finally {
            setBusy(false);
          }
        }}
        className={cx("press mt-3 inline-flex h-11 items-center gap-2 rounded-card bg-neel px-5 font-semibold text-on-neel hover:bg-neel-hover disabled:opacity-60")}>
        {t("approve")}
      </button>
    </li>
  );
}
