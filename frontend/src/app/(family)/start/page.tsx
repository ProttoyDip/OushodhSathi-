"use client";

import { ArrowRight, Check, Copy, KeyRound, MessageCircle } from "lucide-react";
import Link from "next/link";
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
const EMAIL = /^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,}$/;

/** Add a family member: creates a private household and keeps its key in this browser. */
export default function StartPage() {
  const [created, setCreated] = useState<{ id: number; link: string } | null>(null);
  return created ? <SaveLink id={created.id} link={created.link} /> : <CreateForm onCreated={setCreated} />;
}

function CreateForm({ onCreated }: { onCreated: (c: { id: number; link: string }) => void }) {
  const t = useTranslations("start");
  const tc = useTranslations("common");
  const tp = useTranslations("passport.conditions");
  const [nameBn, setNameBn] = useState("");
  const [nameEn, setNameEn] = useState("");
  const [age, setAge] = useState("");
  const [district, setDistrict] = useState("");
  const [conditions, setConditions] = useState<string[]>([]);
  const [email, setEmail] = useState("");
  const [emailOptIn, setEmailOptIn] = useState(false);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();

  const name = nameEn.trim() || nameBn.trim();
  const ageNum = Number(age);
  const emailOk = !email.trim() || EMAIL.test(email.trim());
  const ready = !!name && Number.isInteger(ageNum) && ageNum >= 18 && ageNum <= 120 && consent && emailOk;
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
        consent: true,
        family_email: email.trim() || null,
        email_opt_in: !!email.trim() && emailOptIn,
      });
      rememberFamilyKey(p.id, p.family_key);
      onCreated({ id: p.id, link: `${window.location.origin}/p/${p.id}?key=${encodeURIComponent(p.family_key)}` });
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
                  <input lang="bn" maxLength={80} value={nameBn} onChange={(e) => setNameBn(e.target.value)} className={field} autoComplete="off" placeholder={t("nameBnPlaceholder")} />
                </label>
                <label className="text-base text-ink-soft">
                  {t("nameEn")}
                  <input lang="en" maxLength={80} value={nameEn} onChange={(e) => setNameEn(e.target.value)} className={field} autoComplete="off" placeholder={t("nameEnPlaceholder")} />
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
                  <input maxLength={60} value={district} onChange={(e) => setDistrict(e.target.value)} className={field} autoComplete="address-level2" placeholder={t("districtPlaceholder")} />
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

              <div className="grid gap-2 border-t border-rule pt-4">
                <label className="text-base text-ink-soft">
                  {t("email")}
                  <input type="email" inputMode="email" maxLength={254} value={email} onChange={(e) => setEmail(e.target.value)}
                    className={field} autoComplete="email" placeholder={t("emailPlaceholder")} aria-invalid={!emailOk} />
                </label>
                {!emailOk && <p className="text-[15px] text-red">{t("emailInvalid")}</p>}
                <Tick checked={emailOptIn && !!email.trim()} disabled={!email.trim()} onChange={setEmailOptIn}>
                  {t("emailOptIn")}
                </Tick>
              </div>

              <div className="border-t border-rule pt-4">
                <Tick checked={consent} onChange={setConsent} required>
                  {t.rich("consent", {
                    privacy: (c) => <Link href="/privacy" target="_blank" className="font-semibold text-neel underline underline-offset-4">{c}</Link>,
                    terms: (c) => <Link href="/terms" target="_blank" className="font-semibold text-neel underline underline-offset-4">{c}</Link>,
                  })}
                </Tick>
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

/** A large, elder-friendly checkbox row (48px target). */
function Tick({ checked, onChange, disabled, required, children }: {
  checked: boolean; onChange: (v: boolean) => void; disabled?: boolean; required?: boolean; children: React.ReactNode;
}) {
  return (
    <label className={cx("flex min-h-12 cursor-pointer items-start gap-3 text-base text-ink", disabled && "cursor-not-allowed opacity-60")}>
      <input type="checkbox" checked={checked} disabled={disabled} required={required}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 h-6 w-6 shrink-0 cursor-pointer accent-[var(--neel)]" />
      <span>{children}</span>
    </label>
  );
}

/** Right after creating the list: the only way back in on another phone is this link, so say so. */
function SaveLink({ id, link }: { id: number; link: string }) {
  const t = useTranslations("start.saved");
  const router = useRouter();
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
    } catch {}
  }

  return (
    <>
      <FamilyHeader back="/" />
      <main className={`mx-auto w-full px-4 pb-16 pt-4 lg:pt-8 ${familyWidth}`}>
        <div {...reveal(0)} className="max-w-[640px]">
          <p className="inline-flex items-center gap-2 rounded-chip bg-green-tint px-3 py-1 text-[15px] font-semibold text-green">
            <Check aria-hidden size={16} strokeWidth={2.75} /> {t("done")}
          </p>
          <h1 className="mt-4 font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t("title")}</h1>
          <p className="mt-2 text-ink-soft">{t("body")}</p>
          <div className="mt-6 rounded-card border border-rule bg-paper p-5">
            <p className="text-[15px] font-semibold text-ink-soft">{t("linkLabel")}</p>
            <p className="mt-1 break-all font-mono text-[15px] text-ink" translate="no">{link}</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <button type="button" onClick={copy} className={buttonStyles.secondary}>
                {copied ? <Check aria-hidden size={18} /> : <Copy aria-hidden size={18} />}
                {copied ? t("copied") : t("copy")}
              </button>
              <a href={`https://wa.me/?text=${encodeURIComponent(`${t("whatsappText")} ${link}`)}`} target="_blank" rel="noopener noreferrer"
                className={buttonStyles.secondary}>
                <MessageCircle aria-hidden size={18} /> {t("whatsapp")}
              </a>
            </div>
            <p className="mt-4 text-[15px] text-ink-faint">{t("warning")}</p>
          </div>
          <button type="button" onClick={() => router.push(`/p/${id}`)} className={cx(buttonStyles.primary, "mt-6")}>
            {t("continue")} <ArrowRight aria-hidden size={22} />
          </button>
        </div>
      </main>
    </>
  );
}
