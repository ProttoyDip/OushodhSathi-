import { ListChecks, ScanText, Stethoscope, Users } from "lucide-react";
import { getLocale, getTranslations } from "next-intl/server";
import { reveal } from "@/lib/reveal";

type Actor = "family" | "ai" | "rules" | "human";

const STEPS: { key: string; actor: Actor }[] = [
  { key: "s1", actor: "family" },
  { key: "s2", actor: "ai" },
  { key: "s3", actor: "rules" },
  { key: "s4", actor: "rules" },
  { key: "s5", actor: "human" },
  { key: "s6", actor: "family" },
];

const ACTOR_ICON = { family: Users, ai: ScanText, rules: ListChecks, human: Stethoscope } as const;

/**
 * Six steps from photos to a checked list, as one stitched path (not six identical cards).
 * Each step says who does it, by icon + word; the clinician step is the only one in indigo,
 * because it is the step everything else waits for.
 */
export async function HowTimeline() {
  const t = await getTranslations("landing");
  const locale = await getLocale();
  const num = (n: number) => n.toLocaleString(locale === "bn" ? "bn-BD" : "en");

  return (
    <ol className="relative mt-10">
      <span aria-hidden className="stitch-y stitch-draw absolute bottom-8 left-[19px] top-8" />
      {STEPS.map(({ key, actor }, i) => {
        const Icon = ACTOR_ICON[actor];
        const human = actor === "human";
        return (
          <li key={key} {...reveal(i * 60)} className="relative grid grid-cols-[40px_minmax(0,1fr)] gap-x-5 py-4">
            <span aria-hidden
              className={`relative grid h-10 w-10 place-items-center rounded-full border-2 font-display text-lg tabular ${
                human ? "border-neel bg-neel text-on-neel" : "border-stitch bg-paper-raised text-ink"}`}>
              {num(i + 1)}
            </span>
            <div className="min-w-0 pt-1">
              <h3 className="flex flex-wrap items-baseline gap-x-2 text-[21px] font-semibold leading-snug text-ink">
                <span className="sr-only">{t("how.step", { n: i + 1 })}: </span>
                {t(`flow.${key}.title`)}
                <span lang={locale === "bn" ? "en" : "bn"} className="text-[16px] font-medium text-ink-faint">{t(`flow.${key}.alt`)}</span>
              </h3>
              <p className="mt-1 max-w-[56ch] text-[17px] leading-relaxed text-ink-soft">{t(`flow.${key}.body`)}</p>
              <p className={`mt-2 inline-flex items-center gap-1.5 text-[14px] font-semibold ${human ? "text-neel" : "text-ink-faint"}`}>
                <Icon aria-hidden size={15} /> {t(`flow.actor.${actor}`)}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
