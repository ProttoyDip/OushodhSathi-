import { ArrowRight, Camera, Check, FileText, Link2, ScrollText } from "lucide-react";
import { getTranslations } from "next-intl/server";
import { StripCard } from "@/components/StripCard";
import { DEMO_ITEMS } from "@/lib/demoData";

const frame = "h-full rounded-[20px] border border-rule-strong bg-paper p-5 shadow-soft";

/** One illustration per step of "how it works", built from the real components and the demo household. */
export async function storyVisuals(): Promise<React.ReactNode[]> {
  const t = await getTranslations("landing.story");
  const generic = (g: string) => (
    <span className="whitespace-nowrap rounded-chip bg-neel-tint px-3 py-1 text-[15px] font-medium text-neel">{g}</span>
  );
  return [
    // 1 photograph
    <div key="v1" className={`${frame} grid place-items-center`}>
      <div className="relative w-full max-w-[320px] rounded-card border-2 border-dashed border-stitch p-6">
        <div className="flex h-24 items-center gap-3 overflow-hidden rounded-card border border-rule bg-paper-raised pr-4">
          <span className="foil perforated h-full w-4" />
          <span className="text-[20px] font-semibold text-ink">Napa</span>
          <span className="text-ink-faint">500 mg</span>
        </div>
        <p className="mt-4 inline-flex items-center gap-2 text-[15px] font-semibold text-ink-soft"><Camera size={17} /> {t("v1")}</p>
      </div>
    </div>,
    // 2 read
    <div key="v2" className={`${frame} grid content-start gap-3 overflow-hidden`}>
      <StripCard item={DEMO_ITEMS.napa} density="compact" titleAs="p" />
      <StripCard item={DEMO_ITEMS.ace} density="compact" titleAs="p" />
    </div>,
    // 3 match
    <div key="v3" className={`${frame} grid content-center gap-4`}>
      {(["Napa", "Ace", "Camlodin"] as const).map((b) => (
        <p key={b} className="flex items-center gap-3 text-[19px] font-semibold text-ink">
          <span className="w-28">{b}</span> <ArrowRight aria-hidden size={18} className="text-ink-faint" />
          {generic(t(b === "Camlodin" ? "amlodipine" : "paracetamol"))}
        </p>
      ))}
      <p className="mt-2 text-[15px] text-ink-faint">{t("v3")}</p>
    </div>,
    // 4 rules
    <div key="v4" className={`${frame} grid content-center`}>
      <div className="rounded-card border border-red bg-paper-raised p-5">
        <p className="inline-flex items-center gap-2 rounded-chip bg-red px-3 py-1 text-[15px] font-semibold text-paper-raised">
          <Link2 size={16} /> {t("v4title")}
        </p>
        <p className="mt-4 text-[18px] leading-relaxed text-ink">{t("v4body")}</p>
        <p className="mt-3 inline-flex items-center gap-2 text-[15px] text-ink-faint"><FileText size={15} /> {t("v4source")}</p>
      </div>
    </div>,
    // 5 confirm
    <div key="v5" className={`${frame} grid content-center gap-4`}>
      <p className="rounded-card border border-rule bg-paper-raised p-4 text-[17px] text-ink-soft">{t("v5note")}</p>
      <p className="inline-flex items-center gap-2 text-[17px] font-semibold text-green">
        <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-green text-paper-raised"><Check size={16} strokeWidth={3} /></span>
        {t("v5done")}
      </p>
    </div>,
    // 6 understand
    <div key="v6" className={`${frame} grid content-center gap-4`}>
      <p className="text-[15px] font-semibold text-ink-faint">{t("v6label")}</p>
      <p lang="bn" className="text-[19px] leading-[1.7] text-ink">{t("v6family")}</p>
      <p className="inline-flex items-center gap-2 text-[15px] font-semibold text-neel"><ScrollText size={16} /> {t("v6passport")}</p>
    </div>,
  ];
}
