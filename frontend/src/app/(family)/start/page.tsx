"use client";

import { ArrowRight, Check, KeyRound } from "lucide-react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { api, ApiError } from "@/lib/api";
import { rememberFamilyKey } from "@/lib/familyKey";
import { cx } from "@/lib/format";
import { reveal } from "@/lib/reveal";

// Stored as these codes; the passport and reviewer screens translate them.
const CONDITIONS = ["hypertension", "type 2 diabetes"] as const;

/** Add a family member: creates a private household and keeps its key in this browser. */
export default function StartPage() {
  const router = useRouter();
  const t = useTranslations("start");
  const tc = useTranslations("common");
  const tp = useTranslations("passport.conditions");
  const [nameBn, setNameBn] = useState("");
  const [nameEn, setNameEn] = useState("");
  const [age, setAge] = useState("");
  const [district, setDistrict] = useState("");
  const [conditions, setConditions] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();

  const name = nameEn.trim() || nameBn.trim();
  const ageNum = Number(age);
  const ready = !!name && Number.isInteger(ageNum) && ageNum >= 18 && ageNum <= 120;
  const field = "mt-1 block h-12 w-full rounded-md border border-rule-strong bg-paper-raised px-3 text-lg text-ink";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!ready) return;
    setBusy(true);
    setError(undefined);
    try {
      const p = await api.createPatient({
        name,
        name_bn: nameBn.trim() || null,
        age: ageNum,
        district: district.trim() || null,
        conditions,
      });
      rememberFamilyKey(p.id, p.family_key);
      router.push(`/p/${p.id}`);
    } catch (err) {
      setBusy(false);
      setError(err instanceof ApiError && err.status === 429 ? tc("errorTooMany") : tc("errorGeneric"));
    }
  }

  return (
    <>
      <FamilyHeader back="/" />
      <main className={`mx-auto w-full px-4 pb-16 pt-4 lg:pt-8 ${familyWidth}`}>
        <div {...reveal(0)}>
          <h1 className="font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t("title")}</h1>
          <p className="mt-2 max-w-[60ch] text-ink-soft">{t("intro")}</p>
        </div>
        <div className="mt-6 grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.8fr)] lg:items-start lg:gap-x-12">
          <div {...reveal(60)}>
            <form onSubmit={submit} className="grid gap-4 rounded-card border border-rule bg-paper p-5 lg:p-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="text-base text-ink-soft">
                  {t("nameBn")}
                  <input lang="bn" value={nameBn} onChange={(e) => setNameBn(e.target.value)} className={field} autoComplete="off" placeholder={t("nameBnPlaceholder")} />
                </label>
                <label className="text-base text-ink-soft">
                  {t("nameEn")}
                  <input lang="en" value={nameEn} onChange={(e) => setNameEn(e.target.value)} className={field} autoComplete="off" placeholder={t("nameEnPlaceholder")} />
                </label>
              </div>
              <p className="-mt-2 text-[15px] text-ink-faint">{t("nameHint")}</p>

              <div className="grid gap-4 sm:grid-cols-[minmax(0,140px)_minmax(0,1fr)]">
                <label className="text-base text-ink-soft">
                  {t("age")}
                  <input required type="number" inputMode="numeric" min={18} max={120} value={age} onChange={(e) => setAge(e.target.value)} className={cx(field, "tabular")} />
                </label>
                <label className="text-base text-ink-soft">
                  {t("district")}
                  <input value={district} onChange={(e) => setDistrict(e.target.value)} className={field} autoComplete="address-level2" placeholder={t("districtPlaceholder")} />
                </label>
              </div>

              <div role="group" aria-labelledby="conditions-label">
                <p id="conditions-label" className="text-base text-ink-soft">{t("conditions")}</p>
                <div className="mt-1.5 flex flex-wrap gap-2">
                  {CONDITIONS.map((c) => {
                    const on = conditions.includes(c);
                    return (
                      <button
                        key={c}
                        type="button"
                        aria-pressed={on}
                        onClick={() => setConditions(on ? conditions.filter((x) => x !== c) : [...conditions, c])}
                        className={cx(
                          "press inline-flex h-12 items-center gap-1.5 rounded-md border px-4 text-base font-semibold transition-colors duration-150",
                          on ? "border-neel bg-neel-tint text-neel" : "border-rule-strong text-ink-soft hover:bg-paper-sunk",
                        )}
                      >
                        {on && <Check aria-hidden size={16} strokeWidth={2.75} />}
                        {tp(c)}
                      </button>
                    );
                  })}
                </div>
              </div>

              {error && <p role="alert" className="rounded-card border border-red-line bg-red-tint p-4 text-red">{error}</p>}
              <button type="submit" disabled={!ready || busy} className={cx(buttonStyles.primary, "mt-2")}>
                {busy ? t("creating") : t("create")}
                {!busy && <ArrowRight aria-hidden size={22} />}
              </button>
            </form>
          </div>

          <aside {...reveal(120)} className="rounded-card border border-dashed border-rule-strong p-5 text-base text-ink-soft">
            <p className="flex items-center gap-2 font-semibold text-ink">
              <KeyRound aria-hidden size={20} className="shrink-0 text-neel" />
              {t("privateTitle")}
            </p>
            <p className="mt-2">{t("privateBody")}</p>
            <p className="mt-3">{t("privateShare")}</p>
          </aside>
        </div>
      </main>
    </>
  );
}
