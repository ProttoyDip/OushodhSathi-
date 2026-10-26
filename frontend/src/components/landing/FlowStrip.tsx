import { cx } from "@/lib/format";

type Actor = "family" | "ai" | "rules" | "human";

const STEPS: { actor: Actor; title: string; bn: string; body: string }[] = [
  { actor: "family", title: "Photograph", bn: "ছবি", body: "Every strip, box and prescription in the house, cut strips included." },
  { actor: "ai", title: "Read", bn: "পড়া", body: "A vision model turns photos into typed items: brand, strength, expiry, confidence." },
  { actor: "rules", title: "Match", bn: "মেলানো", body: "Each Bangladeshi brand maps to its generic. Unknown brands are searched on Bangladeshi medicine sites and marked unverified." },
  { actor: "rules", title: "Check", bn: "নিয়ম", body: "A deterministic engine flags duplicates, same-class pairs, interactions, Beers 65+ drugs and expired strips." },
  { actor: "human", title: "Confirm", bn: "নিশ্চিত", body: "A pharmacist or doctor confirms or dismisses each finding, with a note, in under 30 seconds." },
  { actor: "family", title: "Understand", bn: "বোঝা", body: "The family sees only confirmed findings in plain Bangla, a weekly report and a printable passport." },
];

const ACTOR: Record<Actor, { label: string; dome: string }> = {
  family: { label: "Family", dome: "bg-paper-raised border-2 border-ink" },
  ai: { label: "AI (perception)", dome: "border border-foil-lo" },
  rules: { label: "Rules (deterministic)", dome: "bg-ink border border-ink" },
  human: { label: "Clinician (judgement)", dome: "bg-neel border border-neel" },
};

const foilDome = { background: "radial-gradient(circle at 34% 30%, var(--foil-hi), var(--foil) 58%, var(--foil-lo))" };

/** The six-step flow drawn as one blister strip: each pocket is a step, coloured by who acts. */
export function FlowStrip() {
  return (
    <div className="mt-12">
      <ul className="mb-6 flex flex-wrap gap-x-6 gap-y-2 text-[15px] text-ink-soft" aria-label="Legend">
        {(Object.keys(ACTOR) as Actor[]).map((a) => (
          <li key={a} className="inline-flex items-center gap-2">
            <span aria-hidden className={cx("block h-4 w-4 rounded-full", ACTOR[a].dome)} style={a === "ai" ? foilDome : undefined} />
            {ACTOR[a].label}
          </li>
        ))}
      </ul>

      <ol className="relative grid gap-0 lg:grid-cols-6">
        {/* the foil strip running behind the pockets */}
        <div aria-hidden className="foil absolute left-[27px] top-0 h-full w-[30px] rounded-md lg:left-0 lg:top-[14px] lg:h-[30px] lg:w-full" />
        {STEPS.map((s, i) => (
          <li key={s.title} className="relative grid grid-cols-[58px_1fr] gap-4 pb-8 lg:block lg:pb-0 lg:pr-5">
            <span
              aria-hidden
              className={cx("relative z-10 mx-auto flex h-[58px] w-[58px] items-center justify-center rounded-full shadow-soft lg:mx-0", ACTOR[s.actor].dome)}
              style={s.actor === "ai" ? foilDome : undefined}
            >
              <span className={cx("tabular font-display text-[24px] leading-none", s.actor === "rules" || s.actor === "human" ? "text-paper" : "text-ink")}>
                {i + 1}
              </span>
            </span>
            <div className="lg:mt-5">
              <p className="flex items-baseline gap-2">
                <span className="text-xl font-semibold text-ink">{s.title}</span>
                <span lang="bn" className="font-bn-display text-[17px] text-ink-soft">{s.bn}</span>
              </p>
              <p className="mt-0.5 text-[13px] font-semibold uppercase tracking-[0.06em] text-ink-faint">{ACTOR[s.actor].label}</p>
              <p className="mt-2 text-[16px] leading-relaxed text-ink-soft">{s.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
