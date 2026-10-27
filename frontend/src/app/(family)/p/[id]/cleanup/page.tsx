"use client";

import { Archive, CalendarX, MessagesSquare, PackageCheck, Undo2, UserRoundX } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { ErrorState, Skeleton } from "@/components/States";
import { api } from "@/lib/api";
import { cx, expiry, genericName } from "@/lib/format";
import { loadThumbs } from "@/lib/thumbs";
import type { CleanupItem } from "@/lib/types";
import { useApi } from "@/lib/useApi";

/** Strips to put away so nobody takes them by mistake: expired, or stopped by the pharmacist. */
export default function CleanupPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const t = useTranslations("cleanup");
  const list = useApi(() => api.cleanup(pid), [pid]);
  const [thumbs, setThumbs] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState<number | null>(null);
  useEffect(() => setThumbs(loadThumbs(pid)), [pid]);

  async function setAside(item: CleanupItem, value: boolean) {
    setBusy(item.id);
    try {
      await api.patchItem(pid, item.id, { set_aside: value });
      list.reload();
    } finally {
      setBusy(null);
    }
  }

  const d = list.data;
  return (
    <>
      <FamilyHeader back={`/p/${pid}`} />
      <main className={`mx-auto w-full px-4 pb-12 pt-4 lg:pt-8 ${familyWidth}`}>
        <h1 className="font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t("title")}</h1>
        <p className="mt-2 max-w-[62ch] text-ink-soft">{t("intro")}</p>
        <div className="mt-4 grid max-w-[62ch] gap-1 rounded-card border border-rule bg-paper-raised p-4 text-base">
          <p className="flex items-start gap-2"><Archive aria-hidden size={20} className="mt-0.5 shrink-0 text-neel" /> {t("tip1")}</p>
          <p className="flex items-start gap-2"><MessagesSquare aria-hidden size={20} className="mt-0.5 shrink-0 text-neel" />
            <span>{t("tip2")} <Link href={`/p/${pid}/questions`} className="font-semibold text-neel underline underline-offset-4">{t("ask")}</Link></span>
          </p>
        </div>

        {list.error ? (
          <div className="mt-6"><ErrorState error={list.error} onRetry={list.reload} /></div>
        ) : !d ? (
          <Skeleton lines={2} className="mt-6" />
        ) : (
          <>
            <h2 className="mt-8 font-semibold">{t("toDo", { count: d.to_set_aside.length })}</h2>
            {d.to_set_aside.length === 0 ? (
              <p className="mt-2 flex items-center gap-2 text-ink-soft"><PackageCheck aria-hidden size={20} className="text-green" /> {t("none")}</p>
            ) : (
              <ul className="mt-3 grid gap-3 md:grid-cols-2">
                {d.to_set_aside.map((it) => (
                  <Card key={it.id} it={it} thumb={thumbs[it.id]}>
                    <button type="button" disabled={busy === it.id} onClick={() => setAside(it, true)} className={cx(buttonStyles.secondary, "w-full border-neel text-neel")}>
                      <Archive aria-hidden size={18} /> {t("done")}
                    </button>
                  </Card>
                ))}
              </ul>
            )}
            {d.set_aside.length > 0 && (
              <>
                <h2 className="mt-8 font-semibold text-ink-soft">{t("putAway", { count: d.set_aside.length })}</h2>
                <ul className="mt-3 grid gap-3 md:grid-cols-2">
                  {d.set_aside.map((it) => (
                    <Card key={it.id} it={it} thumb={thumbs[it.id]} muted>
                      <button type="button" disabled={busy === it.id} onClick={() => setAside(it, false)} className={cx(buttonStyles.quiet, "px-2")}>
                        <Undo2 aria-hidden size={18} /> {t("undo")}
                      </button>
                    </Card>
                  ))}
                </ul>
              </>
            )}
          </>
        )}
      </main>
    </>
  );
}

function Card({ it, thumb, muted, children }: { it: CleanupItem; thumb?: string; muted?: boolean; children: React.ReactNode }) {
  const t = useTranslations("cleanup");
  const locale = useLocale();
  return (
    <li className={cx("rounded-card border border-rule bg-paper-raised p-4", muted && "opacity-75")}>
      <div className="flex items-start gap-3">
        {thumb ? (
          // eslint-disable-next-line @next/next/no-img-element -- this phone's own photo, never uploaded or stored
          <img src={thumb} alt="" className="h-16 w-16 shrink-0 rounded-md border border-rule object-cover" />
        ) : (
          <span aria-hidden className="foil h-16 w-16 shrink-0 rounded-md border border-foil-lo" />
        )}
        <div className="min-w-0 flex-1">
          <p className="text-[20px] font-semibold leading-tight">{it.brand} <span className="tabular text-base font-medium text-ink-soft">{it.strength}</span></p>
          {it.generic && <p className="text-base text-ink-soft">{genericName(it.generic, locale)}</p>}
          <p className="mt-1.5 inline-flex items-center gap-1.5 rounded-chip border border-amber-line bg-amber-tint px-3 py-0.5 text-[15px] font-semibold text-amber">
            {it.reason === "expired" ? <CalendarX aria-hidden size={15} /> : <UserRoundX aria-hidden size={15} />}
            {it.reason === "expired" ? t("expired", { date: expiry(it.expiry, locale) }) : t("stopped", { name: it.stopped_by ?? "" })}
          </p>
        </div>
      </div>
      <div className="mt-3">{children}</div>
    </li>
  );
}
