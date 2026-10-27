"use client";

import { Camera, Check, Images, Lock, ShieldCheck, X } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useRef, useState } from "react";
import { buttonStyles, FamilyHeader, familyWidth } from "@/components/Chrome";
import { api, ApiError } from "@/lib/api";
import { cx } from "@/lib/format";
import { saveThumbs } from "@/lib/thumbs";
import { useApi } from "@/lib/useApi";
import { reveal } from "@/lib/reveal";

const MAX = 12;

export default function ScanPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const router = useRouter();
  const t = useTranslations("scan");
  const tc = useTranslations("common");
  const patient = useApi(() => api.patient(pid), [pid]);
  const health = useApi(() => api.health(), []);
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string>();
  const cameraRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);

  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files]);
  useEffect(() => () => previews.forEach(URL.revokeObjectURL), [previews]);

  useEffect(() => {
    if (!busy) return;
    const timer = setInterval(() => setStep((s) => Math.min(s + 1, 2)), 1700);
    return () => clearInterval(timer);
  }, [busy]);

  const demoShelf = health.data?.demo_mode && health.data.providers.vision.length === 0;

  function add(list: FileList | null) {
    if (!list) return;
    const next = [...files, ...Array.from(list)];
    if (next.length > MAX) setError(t("tooMany"));
    setFiles(next.slice(0, MAX));
  }

  async function read(photos: File[]) {
    setBusy(true);
    setStep(0);
    setError(undefined);
    try {
      const res = await api.scan(pid, photos);
      const thumbs: Record<number, string> = {};
      for (const it of res.items) if (it.thumbnail) thumbs[it.id] = it.thumbnail;
      saveThumbs(pid, thumbs);
      router.push(`/p/${pid}/confirm${res.mode === "demo" ? "?demo=1" : ""}`);
    } catch (e) {
      setBusy(false);
      setError(e instanceof ApiError && e.status === 0 ? tc("errorOffline")
        : e instanceof ApiError && e.status === 429 ? tc("errorTooMany") : t("failed"));
    }
  }

  const steps = [t("reading1"), t("reading2"), t("reading3")];

  return (
    <>
      <FamilyHeader back={`/p/${pid}`} demo={patient.data?.is_demo} />
      <main className={`mx-auto w-full px-4 pb-40 pt-4 lg:pb-32 lg:pt-8 ${familyWidth}`}>
        <h1 className="font-bn-display text-[32px] leading-[1.2] lg:text-[40px]">{t("title")}</h1>
        <p className="mt-2 max-w-[65ch] text-ink-soft">{t("intro")}</p>

        {busy ? (
          <section aria-live="polite" className="mt-8 rounded-card border border-rule bg-paper-raised p-6 lg:max-w-[560px]">
            <ol className="grid gap-4">
              {steps.map((label, i) => (
                <li key={label} className={cx("flex items-center gap-3 transition-colors duration-200", i > step ? "text-ink-faint" : "text-ink")}>
                  <span
                    aria-hidden
                    className={cx(
                      "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2",
                      i < step ? "border-neel bg-neel text-on-neel" : i === step ? "border-neel" : "border-rule",
                    )}
                  >
                    {i < step ? <Check size={16} strokeWidth={3} /> : i === step ? (
                      <span className="block h-2.5 w-2.5 rounded-full bg-neel" style={{ animation: "breathe 1.4s ease-in-out infinite" }} />
                    ) : null}
                  </span>
                  <span className={i === step ? "font-semibold" : undefined}>{label}</span>
                </li>
              ))}
            </ol>
            <p className="mt-5 text-base text-ink-soft">{t("readingNote")}</p>
          </section>
        ) : (
          <div className="grid grid-cols-[minmax(0,1fr)] lg:mt-8 lg:grid-cols-[minmax(0,0.75fr)_minmax(0,1.25fr)] lg:items-start lg:gap-10">
            <section {...reveal(0)} aria-labelledby="tips-h" className="mt-6 rounded-card border border-rule bg-paper-raised p-5 lg:mt-0">
              <h2 id="tips-h" className="font-semibold">{t("tipsTitle")}</h2>
              <ul className="mt-2 grid gap-1.5">
                {[t("tip1"), t("tip2"), t("tip3"), t("tip4")].map((tip) => (
                  <li key={tip} className="flex items-start gap-2.5">
                    <Check aria-hidden size={20} className="mt-1 shrink-0 text-neel" />
                    {tip}
                  </li>
                ))}
              </ul>
            </section>

            <div {...reveal(90)}>
            <div className="mt-6 grid grid-cols-2 gap-3 lg:mt-0">
              <button type="button" onClick={() => cameraRef.current?.click()} className={cx(buttonStyles.secondary, "min-h-[88px] flex-col gap-1.5")}>
                <Camera aria-hidden size={26} />
                {t("takePhoto")}
              </button>
              <button type="button" onClick={() => galleryRef.current?.click()} className={cx(buttonStyles.secondary, "min-h-[88px] flex-col gap-1.5")}>
                <Images aria-hidden size={26} />
                {t("choosePhotos")}
              </button>
            </div>
            <input ref={cameraRef} type="file" accept="image/*" capture="environment" className="sr-only" tabIndex={-1} aria-hidden onChange={(e) => { add(e.target.files); e.target.value = ""; }} />
            <input ref={galleryRef} type="file" accept="image/*" multiple className="sr-only" tabIndex={-1} aria-hidden onChange={(e) => { add(e.target.files); e.target.value = ""; }} />

            <p className="mt-4 text-base text-ink-soft" aria-live="polite">{t("selected", { count: files.length })}</p>
            {files.length > 0 && (
              <ul aria-label={t("photosLabel")} className="mt-3 grid grid-cols-3 gap-3 lg:grid-cols-4">
                {previews.map((src, i) => (
                  <li key={src} className="relative aspect-square overflow-hidden rounded-card border border-rule bg-paper-sunk" style={{ animation: `assemble 220ms var(--ease-out-quint) ${i * 40}ms both` }}>
                    {/* eslint-disable-next-line @next/next/no-img-element -- local object URL preview */}
                    <img src={src} alt="" className="h-full w-full object-cover" />
                    <button
                      type="button"
                      aria-label={t("removePhoto")}
                      onClick={() => setFiles(files.filter((_, j) => j !== i))}
                      className="absolute right-1 top-1 flex h-11 w-11 items-center justify-center rounded-full bg-paper-raised/95 text-ink shadow-soft"
                    >
                      <X aria-hidden size={20} />
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {error && <p role="alert" className="mt-4 rounded-card border border-red-line bg-red-tint p-4 text-red">{error}</p>}

            <p className="mt-6 flex items-start gap-2 text-base text-ink-soft">
              <Lock aria-hidden size={18} className="mt-1 shrink-0" />
              {t("privacy")}
            </p>
            </div>
          </div>
        )}
      </main>

      {!busy && (
        <div className="no-print fixed inset-x-0 bottom-0 border-t border-rule bg-paper/95 px-4 pb-[max(16px,env(safe-area-inset-bottom))] pt-3 backdrop-blur-sm">
          <div className={`mx-auto grid gap-2 lg:flex lg:flex-row-reverse lg:items-center lg:justify-start ${familyWidth}`}>
            <button type="button" disabled={files.length === 0} onClick={() => read(files)} className={`${buttonStyles.primary} lg:w-auto lg:min-w-[320px]`}>
              <ShieldCheck aria-hidden size={22} />
              {t("read")}
            </button>
            {demoShelf && files.length === 0 && (
              <button
                type="button"
                onClick={() => read([new File([new Uint8Array([0xff, 0xd8, 0xff, 0xd9])], "demo-shelf.jpg", { type: "image/jpeg" })])}
                className={buttonStyles.quiet}
              >
                {t("useDemo")}
              </button>
            )}
          </div>
        </div>
      )}
    </>
  );
}
