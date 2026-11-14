import { useLocale, useTranslations } from "next-intl";
import { cx } from "@/lib/format";
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

const DOME: Record<Actor, string> = {
  family: "bg-paper-raised border-2 border-ink",
  ai: "border border-foil-lo",
  rules: "bg-ink border border-ink",
  human: "bg-neel border border-neel",
};

const foilDome = { background: "radial-gradient(circle at 34% 30%, var(--foil-hi), var(--foil) 58%, var(--foil-lo))" };

/** The six-step flow drawn as one blister strip: each pocket is a step, coloured by who acts. */
export function FlowStrip() {
  const t = useTranslations("landing.flow");
  const altLang = useLocale() === "bn" ? "en" : "bn";
  return (
    <div className="mt-12">
      <ul className="mb-6 flex flex-wrap gap-x-6 gap-y-2 text-[15px] text-ink-soft" aria-label={t("legend")}>
        {(Object.keys(DOME) as Actor[]).map((a) => (
          <li key={a} className="inline-flex items-center gap-2">
            <span aria-hidden className={cx("block h-4 w-4 rounded-full", DOME[a])} style={a === "ai" ? foilDome : undefined} />
            {t(`actor.${a}`)}
          </li>
        ))}
      </ul>

      <ol className="relative grid gap-0 lg:grid-cols-6">
        {/* the foil strip running behind the pockets */}
        <div aria-hidden className="foil absolute left-[27px] top-0 h-full w-[30px] rounded-md lg:left-0 lg:top-[14px] lg:h-[30px] lg:w-full" />
        {STEPS.map((s, i) => (
          <li key={s.key} {...reveal(i * 80)} className="relative grid grid-cols-[58px_1fr] gap-4 pb-8 lg:block lg:pb-0 lg:pr-5">
            <span
              aria-hidden
              className={cx("relative z-10 mx-auto flex h-[58px] w-[58px] items-center justify-center rounded-full shadow-soft lg:mx-0", DOME[s.actor])}
              style={s.actor === "ai" ? foilDome : undefined}
            >
              <span className={cx("tabular font-display text-[24px] leading-none", s.actor === "rules" || s.actor === "human" ? "text-paper" : "text-ink")}>
                {i + 1}
              </span>
            </span>
            <div className="lg:mt-5">
              <p className="flex items-baseline gap-2">
                <span className="text-xl font-semibold text-ink">{t(`${s.key}.title`)}</span>
                <span lang={altLang} className={cx("text-[17px] text-ink-soft", altLang === "bn" ? "font-bn-display" : "font-display italic")}>{t(`${s.key}.alt`)}</span>
              </p>
              <p className="mt-0.5 text-[13px] font-semibold uppercase tracking-[0.06em] text-ink-faint">{t(`actor.${s.actor}`)}</p>
              <p className="mt-2 text-[16px] leading-relaxed text-ink-soft">{t(`${s.key}.body`)}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
