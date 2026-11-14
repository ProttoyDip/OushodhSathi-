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
// who does each step, told by icon + word; the clinician step is the one in indigo
const ACTOR_STYLE: Record<Actor, string> = {
  family: "border-rule-strong text-ink-soft",
  ai: "border-rule-strong text-ink-soft",
  rules: "border-rule-strong text-ink-soft",
  human: "border-neel bg-neel-tint text-neel",
};

/**
 * Six steps from photos to a checked list. A numbered vertical timeline on the kantha-stitch
 * rail on phones; a 3 × 2 grid of the same cards on wide screens.
 * Layout after 21st.dev "Vertical How It Works Timeline".
 */
export async function HowTimeline() {
  const t = await getTranslations("landing");
  const locale = await getLocale();
  const num = (n: number) => n.toLocaleString(locale === "bn" ? "bn-BD" : "en");

  return (
    <ol className="relative mt-12 grid gap-5 pl-12 lg:grid-cols-3 lg:gap-6 lg:pl-0">
      <span aria-hidden className="stitch-y absolute bottom-6 left-[19px] top-6 lg:hidden" />
      {STEPS.map(({ key, actor }, i) => {
        const Icon = ACTOR_ICON[actor];
        return (
          <li key={key} {...reveal(i * 70)} className="relative">
            <span aria-hidden
              className="absolute -left-12 top-5 grid h-10 w-10 place-items-center rounded-full border-2 border-stitch bg-paper font-display text-lg tabular text-ink lg:hidden">
              {num(i + 1)}
            </span>
            <article className="flex h-full flex-col rounded-card border border-rule bg-paper p-5 lg:p-6">
              <div className="flex items-center justify-between gap-3">
                <span className="hidden font-display text-[40px] leading-none tabular text-stitch lg:block" aria-hidden>
                  {num(i + 1).padStart(2, locale === "bn" ? "০" : "0")}
                </span>
                <span className={`inline-flex items-center gap-1.5 rounded-chip border px-3 py-1 text-[14px] font-semibold ${ACTOR_STYLE[actor]}`}>
                  <Icon aria-hidden size={15} /> {t(`flow.actor.${actor}`)}
                </span>
              </div>
              <h3 className="mt-4 text-[22px] font-semibold leading-tight text-ink">
                <span className="sr-only">{t("how.step", { n: i + 1 })}: </span>
                {t(`flow.${key}.title`)}
                <span lang={locale === "bn" ? "en" : "bn"} className="ml-2 text-[17px] font-medium text-ink-faint">
                  {t(`flow.${key}.alt`)}
                </span>
              </h3>
              <p className="mt-2 text-[17px] leading-relaxed text-ink-soft">{t(`flow.${key}.body`)}</p>
            </article>
          </li>
        );
      })}
    </ol>
  );
}
