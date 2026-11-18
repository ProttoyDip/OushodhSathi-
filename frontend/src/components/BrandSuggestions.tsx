"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { genericName } from "@/lib/format";

type Suggestion = { brand: string; generic: string; strength: string | null };

/** "Is it ...?" for a brand the app did not recognise. Tapping one only fills in the name, as if the
 * family had typed it; the app then matches it as usual and the pharmacist still reviews the list. */
export function BrandSuggestions({ brand, onPick }: { brand: string; onPick: (brand: string) => void }) {
  const t = useTranslations("confirm.suggest");
  const locale = useLocale();
  const [list, setList] = useState<Suggestion[]>([]);

  useEffect(() => {
    let live = true;
    api.suggestBrands(brand).then((s) => live && setList(s)).catch(() => live && setList([]));
    return () => { live = false; };
  }, [brand]);

  if (list.length === 0) return null;
  return (
    <div className="rounded-card border border-rule bg-paper p-3">
      <p className="text-[15px] font-semibold text-ink">{t("title")}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {list.map((s) => (
          <button key={s.brand} type="button" onClick={() => onPick(s.brand)}
            className="press inline-flex min-h-11 items-center gap-1.5 whitespace-nowrap rounded-chip border border-rule-strong px-4 text-[15px] font-semibold text-ink hover:border-neel hover:text-neel">
            {s.brand}
            <span className="font-normal text-ink-faint">· {genericName(s.generic, locale)}</span>
          </button>
        ))}
      </div>
      <p className="mt-2 text-[13px] text-ink-faint">{t("note")}</p>
    </div>
  );
}
