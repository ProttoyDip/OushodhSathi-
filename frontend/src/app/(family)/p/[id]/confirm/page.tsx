"use client";

import { Check, CircleCheck, Clock, Cpu, FlaskConical, Pencil, Plus, Send, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Suspense, useEffect, useRef, useState } from "react";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { ErrorState, Skeleton } from "@/components/States";
import { StripCard } from "@/components/StripCard";
import { api } from "@/lib/api";
import { cx } from "@/lib/format";
import { clearThumbs, loadThumbs } from "@/lib/thumbs";
import type { MedicineItem, Slot } from "@/lib/types";
import { useApi } from "@/lib/useApi";

export default function ConfirmPage() {
  return (
    <Suspense>
      <Confirm />
    </Suspense>
  );
}

const SLOTS: Slot[] = ["morning", "noon", "night"];

/** When a medicine is taken and how many are left: feeds the passport and the refill warning. */
type Plan = { schedule: Slot[]; pills_left: number | null };

const planOf = (item: MedicineItem): Plan => ({ schedule: item.schedule, pills_left: item.pills_left });

const planPatch = (plan: Plan) => ({
  schedule: plan.schedule,
  pills_left: plan.pills_left,
  doses_per_day: plan.schedule.length || null,
});

function Confirm() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const router = useRouter();
  const demo = useSearchParams().get("demo") === "1";
  const t = useTranslations("confirm");
  const ts = useTranslations("scan");
  const tc = useTranslations("common");
  const tm = useTranslations("models");
  const patient = useApi(() => api.patient(pid), [pid]);
  const items = useApi(() => api.items(pid), [pid]);
  const [thumbs, setThumbs] = useState<Record<number, string>>({});
  const [editing, setEditing] = useState<number | null>(null);
  const [editingTimes, setEditingTimes] = useState<number | null>(null);
  const [plans, setPlans] = useState<Record<number, Plan>>({});
  // lift Sathi's button above the fixed send bar so it never covers the primary action
  const barRef = useRef<HTMLDivElement>(null);
  const hasBar = (items.data?.length ?? 0) > 0;
  useEffect(() => {
    const bar = barRef.current;
    if (!bar) return;
    const root = document.documentElement;
    const sync = () => root.style.setProperty("--sathi-offset", `${bar.offsetHeight + 12}px`);
    sync();
    const ro = new ResizeObserver(sync);
    ro.observe(bar);
    return () => { ro.disconnect(); root.style.removeProperty("--sathi-offset"); };
  }, [hasBar]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => setThumbs(loadThumbs(pid)), [pid]);

  const list = items.data ?? [];
  const open = list.filter((i) => !i.confirmed);
  // which AI model actually read these photos (demo items carry no model)
  const readBy = Array.from(new Set(open.map((i) => i.model_id).filter((m): m is string => !!m && !m.startsWith("demo"))));
  const done = list.filter((i) => i.confirmed);

  function replace(updated: MedicineItem) {
    items.setData(list.map((i) => (i.id === updated.id ? updated : i)));
  }

  const plan = (item: MedicineItem) => plans[item.id] ?? planOf(item);
  // functional update: two quick taps in a row must both count
  const setPlan = (item: MedicineItem, change: (p: Plan) => Plan) =>
    setPlans((all) => ({ ...all, [item.id]: change(all[item.id] ?? planOf(item)) }));

  async function save(item: MedicineItem, fields: Partial<MedicineItem>) {
    replace({ ...item, ...fields }); // optimistic
    try {
      replace(await api.patchItem(pid, item.id, fields));
      return true;
    } catch {
      replace(item);
      setError(tc("errorGeneric"));
      return false;
    }
  }

  const confirm = (item: MedicineItem) => save(item, { confirmed: true, ...planPatch(plan(item)) });

  async function send() {
    setSending(true);
    try {
      await api.check(pid);
      clearThumbs(pid);
      router.push(`/p/${pid}/status`);
    } catch {
      setSending(false);
      setError(tc("errorGeneric"));
    }
  }

  return (
    <>
      <FamilyHeader back={`/p/${pid}`} demo={patient.data?.is_demo} />
      <main className={`mx-auto w-full px-4 pb-44 pt-4 lg:pb-36 lg:pt-8 ${familyWidth}`}>
        <h1 className="font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t("title")}</h1>
        <p className="mt-2 max-w-[65ch] text-ink-soft">{t("intro")}</p>
        {demo && (
          <p className="mt-4 flex items-start gap-2 rounded-card border border-dashed border-rule-strong p-4 text-base text-ink-soft lg:max-w-[720px]">
            <FlaskConical aria-hidden size={18} className="mt-1 shrink-0" />
            {ts("demoNote")}
          </p>
        )}
        {readBy.length > 0 && (
          <p className="mt-3 flex flex-wrap items-center gap-2 text-base text-ink-soft">
            <Cpu aria-hidden size={18} className="shrink-0 text-neel" />
            {t("readBy", { model: readBy.join(", ") })}
            <Link href={`/models?from=/p/${pid}/confirm`} className="text-[15px] font-medium text-neel underline">{tm("title")}</Link>
          </p>
        )}

        {items.error ? (
          <div className="mt-6"><ErrorState error={items.error} onRetry={items.reload} /></div>
        ) : items.loading && !items.data ? (
          <Skeleton lines={4} className="mt-6" />
        ) : list.length === 0 ? (
          <p className="mt-8 rounded-card border border-rule bg-paper-raised p-5 text-ink-soft">{t("empty")}</p>
        ) : (
          <ul className="mt-6 grid gap-4 md:grid-cols-2">
            {open.map((item, i) => (
              <li key={item.id} style={{ animation: `assemble 240ms var(--ease-out-quint) ${i * 110}ms both` }}>
                <StripCard item={{ ...item, thumbnail: thumbs[item.id] }}>
                  {editing === item.id ? (
                    <EditForm
                      pid={pid}
                      item={item}
                      onCancel={() => setEditing(null)}
                      onSaved={(u) => { replace(u); setEditing(null); }}
                      onRemoved={() => { items.setData(list.filter((x) => x.id !== item.id)); setEditing(null); }}
                    />
                  ) : (
                    <div className="grid gap-4">
                    <DoseTimes idPrefix={`plan-${item.id}`} plan={plan(item)} onChange={(p) => setPlan(item, p)} />
                    <div className="flex gap-2">
                      <button type="button" onClick={() => confirm(item)} className={cx(buttonStyles.secondary, "flex-1 whitespace-nowrap border-neel px-3 text-neel")}>
                        <Check aria-hidden size={20} strokeWidth={2.5} />
                        {t("correct")}
                      </button>
                      <button type="button" onClick={() => setEditing(item.id)} className={cx(buttonStyles.quiet, "whitespace-nowrap px-3")}>
                        <Pencil aria-hidden size={18} />
                        {t("edit")}
                      </button>
                    </div>
                    </div>
                  )}
                </StripCard>
              </li>
            ))}
          </ul>
        )}

        {done.length > 0 && (
          <section aria-labelledby="done-h" className="mt-10">
            <h2 id="done-h" className="flex items-center gap-2 text-lg font-semibold text-ink-soft">
              <CircleCheck aria-hidden size={20} className="text-green" />
              {t("alreadyConfirmed")}
            </h2>
            <ul className="mt-3 grid gap-3 md:grid-cols-2">
              {done.map((item) => (
                <li key={item.id} style={{ animation: "settle 220ms var(--ease-out-quint) both" }}>
                  <StripCard item={{ ...item, thumbnail: thumbs[item.id] }} density="compact">
                    {editingTimes === item.id ? (
                      <div className="grid gap-3">
                        <DoseTimes idPrefix={`times-${item.id}`} plan={plan(item)} onChange={(p) => setPlan(item, p)} />
                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={async () => { if (await save(item, planPatch(plan(item)))) setEditingTimes(null); }}
                            className={cx(buttonStyles.secondary, "flex-1 border-neel text-neel")}
                          >
                            <Check aria-hidden size={20} />{t("save")}
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setPlans((all) => Object.fromEntries(Object.entries(all).filter(([k]) => Number(k) !== item.id)));
                              setEditingTimes(null);
                            }}
                            className={buttonStyles.quiet}
                          >
                            {t("cancel")}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-wrap items-center justify-between gap-x-3">
                        <p className="flex items-center gap-1.5 text-base text-ink-soft">
                          <Clock aria-hidden size={16} className="shrink-0" />
                          {item.schedule.length ? item.schedule.map((s) => t(s)).join(" · ") : t("asNeeded")}
                        </p>
                        <button type="button" onClick={() => setEditingTimes(item.id)} className={cx(buttonStyles.quiet, "px-2")}>
                          <Pencil aria-hidden size={16} />{t("editTimes")}
                        </button>
                      </div>
                    )}
                  </StripCard>
                </li>
              ))}
            </ul>
          </section>
        )}

        <AddManual pid={pid} onAdded={(it) => items.setData([...list, it])} />
        {error && <p role="alert" className="mt-4 rounded-card border border-red-line bg-red-tint p-4 text-red">{error}</p>}
      </main>

      {list.length > 0 && (
        <div ref={barRef} className="no-print fixed inset-x-0 bottom-0 border-t border-rule bg-paper/95 px-4 pb-[max(16px,env(safe-area-inset-bottom))] pt-3 backdrop-blur-sm">
          <div className={`mx-auto lg:flex lg:items-center lg:justify-end lg:gap-6 ${familyWidth}`}>
            <p className="mb-2 text-center text-base text-ink-soft lg:mb-0" aria-live="polite">{t("remaining", { count: open.length })}</p>
            <button type="button" disabled={open.length > 0 || sending} onClick={send} className={`${buttonStyles.primary} lg:w-auto lg:min-w-[320px]`}>
              <Send aria-hidden size={22} />
              {sending ? t("sending") : t("send")}
            </button>
          </div>
        </div>
      )}
    </>
  );
}

function DoseTimes({ idPrefix, plan, onChange }: { idPrefix: string; plan: Plan; onChange: (change: (p: Plan) => Plan) => void }) {
  const t = useTranslations("confirm");
  const toggle = (slot: Slot) =>
    onChange((p) => {
      const on = new Set(p.schedule);
      if (on.has(slot)) on.delete(slot);
      else on.add(slot);
      return { ...p, schedule: SLOTS.filter((s) => on.has(s)) };
    });
  return (
    <div className="grid gap-3">
      <div role="group" aria-labelledby={`${idPrefix}-when`}>
        <p id={`${idPrefix}-when`} className="text-base text-ink-soft">{t("whenTaken")}</p>
        <div className="mt-2.5 grid grid-cols-3 gap-2">
          {SLOTS.map((slot) => {
            const on = plan.schedule.includes(slot);
            return (
              <button
                key={slot}
                type="button"
                aria-pressed={on}
                onClick={() => toggle(slot)}
                className={cx(
                  "press relative inline-flex h-12 min-w-0 items-center justify-center rounded-md border px-1 text-base font-semibold transition-colors duration-150",
                  on ? "border-2 border-neel bg-neel-tint text-neel" : "border-rule-strong text-ink-soft hover:bg-paper-sunk",
                )}
              >
                {/* the tick sits on the corner so the label always has the chip's full width */}
                {on && (
                  <span aria-hidden className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-neel text-on-neel shadow-soft">
                    <Check size={13} strokeWidth={3} />
                  </span>
                )}
                <span className="truncate">{t(slot)}</span>
              </button>
            );
          })}
        </div>
        {plan.schedule.length === 0 && <p className="mt-1.5 text-[15px] text-ink-faint">{t("asNeededHint")}</p>}
      </div>
      <label htmlFor={`${idPrefix}-pills`} className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 text-base text-ink-soft">
        {t("pillsLeft")}
        <input
          id={`${idPrefix}-pills`}
          type="number"
          inputMode="numeric"
          min={0}
          max={999}
          value={plan.pills_left ?? ""}
          onChange={(e) => {
            const n = e.target.value === "" ? null : Math.max(0, Math.min(999, Math.round(Number(e.target.value))));
            onChange((p) => ({ ...p, pills_left: n !== null && Number.isFinite(n) ? n : null }));
          }}
          className="tabular block h-12 w-24 rounded-md border border-rule-strong bg-paper px-3 text-lg text-ink"
        />
      </label>
    </div>
  );
}

function EditForm({ pid, item, onCancel, onSaved, onRemoved }: {
  pid: number;
  item: MedicineItem;
  onCancel: () => void;
  onSaved: (i: MedicineItem) => void;
  onRemoved: () => void;
}) {
  const t = useTranslations("confirm");
  const [brand, setBrand] = useState(item.brand);
  const [strength, setStrength] = useState(item.strength ?? "");
  const [busy, setBusy] = useState(false);
  const field = "mt-1 block h-12 w-full rounded-md border border-rule-strong bg-paper px-3 text-lg text-ink";
  return (
    <form
      className="grid gap-3"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        try {
          onSaved(await api.patchItem(pid, item.id, { brand: brand.trim(), strength: strength.trim() || null, confirmed: true }));
        } finally {
          setBusy(false);
        }
      }}
    >
      <label className="text-base text-ink-soft">
        {t("brandLabel")}
        <input required value={brand} onChange={(e) => setBrand(e.target.value)} className={field} autoComplete="off" />
      </label>
      <label className="text-base text-ink-soft">
        {t("strengthLabel")}
        <input value={strength} onChange={(e) => setStrength(e.target.value)} className={`${field} tabular`} autoComplete="off" />
      </label>
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={busy || !brand.trim()} className={cx(buttonStyles.secondary, "flex-1 border-neel text-neel")}>
          <Check aria-hidden size={20} />{t("save")}
        </button>
        <button type="button" onClick={onCancel} className={buttonStyles.quiet}>{t("cancel")}</button>
      </div>
      <button
        type="button"
        onClick={async () => { await api.deleteItem(pid, item.id); onRemoved(); }}
        className={cx(buttonStyles.quiet, "justify-start px-0 text-red")}
      >
        <Trash2 aria-hidden size={18} />{t("remove")}
      </button>
    </form>
  );
}

function AddManual({ pid, onAdded }: { pid: number; onAdded: (i: MedicineItem) => void }) {
  const t = useTranslations("confirm");
  const [brand, setBrand] = useState("");
  const [strength, setStrength] = useState("");
  const field = "block h-12 w-full rounded-md border border-rule-strong bg-paper-raised px-3 text-lg text-ink";
  return (
    <details className="group mt-10 rounded-card border border-rule lg:max-w-[560px]">
      <summary className="flex min-h-14 cursor-pointer list-none items-center gap-2 px-4 font-semibold text-ink">
        <Plus aria-hidden size={20} className="transition-transform group-open:rotate-45" />
        {t("addManual")}
      </summary>
      <form
        className="grid gap-3 border-t border-rule p-4"
        onSubmit={async (e) => {
          e.preventDefault();
          if (!brand.trim()) return;
          onAdded(await api.addItem(pid, { brand: brand.trim(), strength: strength.trim() || null, source: "manual" }));
          setBrand("");
          setStrength("");
        }}
      >
        <label className="text-base text-ink-soft">{t("brandLabel")}
          <input value={brand} onChange={(e) => setBrand(e.target.value)} className={`${field} mt-1`} autoComplete="off" />
        </label>
        <label className="text-base text-ink-soft">{t("strengthLabel")}
          <input value={strength} onChange={(e) => setStrength(e.target.value)} className={`${field} tabular mt-1`} autoComplete="off" />
        </label>
        <button type="submit" disabled={!brand.trim()} className={buttonStyles.secondary}>{t("add")}</button>
      </form>
    </details>
  );
}
