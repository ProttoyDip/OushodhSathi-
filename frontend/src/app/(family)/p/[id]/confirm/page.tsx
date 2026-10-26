"use client";

import { Check, CircleCheck, Cpu, FlaskConical, Pencil, Plus, Send, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Suspense, useEffect, useState } from "react";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { ErrorState, Skeleton } from "@/components/States";
import { StripCard } from "@/components/StripCard";
import { api } from "@/lib/api";
import { cx } from "@/lib/format";
import { clearThumbs, loadThumbs } from "@/lib/thumbs";
import type { MedicineItem } from "@/lib/types";
import { useApi } from "@/lib/useApi";

export default function ConfirmPage() {
  return (
    <Suspense>
      <Confirm />
    </Suspense>
  );
}

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

  async function confirm(item: MedicineItem) {
    replace({ ...item, confirmed: true }); // optimistic
    try {
      replace(await api.patchItem(item.id, { confirmed: true }));
    } catch {
      replace(item);
      setError(tc("errorGeneric"));
    }
  }

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
            <Link href="/models" className="text-[15px] font-medium text-neel underline">{tm("title")}</Link>
          </p>
        )}

        {items.error ? (
          <div className="mt-6"><ErrorState error={items.error} onRetry={items.reload} /></div>
        ) : items.loading && !items.data ? (
          <Skeleton lines={4} className="mt-6" />
        ) : list.length === 0 ? (
          <p className="mt-8 rounded-card border border-rule bg-paper-raised p-5 text-ink-soft">{t("empty")}</p>
        ) : (
          <ul className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {open.map((item, i) => (
              <li key={item.id} style={{ animation: `assemble 240ms var(--ease-out-quint) ${i * 110}ms both` }}>
                <StripCard item={{ ...item, thumbnail: thumbs[item.id] }}>
                  {editing === item.id ? (
                    <EditForm
                      item={item}
                      onCancel={() => setEditing(null)}
                      onSaved={(u) => { replace(u); setEditing(null); }}
                      onRemoved={() => { items.setData(list.filter((x) => x.id !== item.id)); setEditing(null); }}
                    />
                  ) : (
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
            <ul className="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {done.map((item) => (
                <li key={item.id} style={{ animation: "settle 220ms var(--ease-out-quint) both" }}>
                  <StripCard item={{ ...item, thumbnail: thumbs[item.id] }} density="compact" />
                </li>
              ))}
            </ul>
          </section>
        )}

        <AddManual pid={pid} onAdded={(it) => items.setData([...list, it])} />
        {error && <p role="alert" className="mt-4 rounded-card border border-red-line bg-red-tint p-4 text-red">{error}</p>}
      </main>

      {list.length > 0 && (
        <div className="no-print fixed inset-x-0 bottom-0 border-t border-rule bg-paper/95 px-4 pb-[max(16px,env(safe-area-inset-bottom))] pt-3 backdrop-blur-sm">
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

function EditForm({ item, onCancel, onSaved, onRemoved }: {
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
          onSaved(await api.patchItem(item.id, { brand: brand.trim(), strength: strength.trim() || null, confirmed: true }));
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
        onClick={async () => { await api.deleteItem(item.id); onRemoved(); }}
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
