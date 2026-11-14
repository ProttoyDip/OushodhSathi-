import { HeroDemo } from "@/components/landing/HeroDemo";

/**
 * The hero object: both sides of the product at once, on the indigo-dyed cloth.
 * The pharmacist's review queue (a real screenshot of /review, light and dark) in a browser
 * frame, with the family's phone in front of it running the live StripCard demo.
 * Layout after 21st.dev "Hero Section with Device Mockups"; no gradients, no glow.
 */
export function ProductFrames({ replayLabel, reviewLabel, phoneLabel }: {
  replayLabel: string; reviewLabel: string; phoneLabel: string;
}) {
  return (
    <div className="dyed-cloth px-4 pb-6 pt-6 sm:px-8 sm:pb-10 sm:pt-10 lg:px-12 lg:pb-14 lg:pt-12">
      <div className="relative md:min-h-[700px] lg:min-h-[720px]">
        {/* browser: the reviewer's side (md and up) */}
        <figure className="relative ml-auto hidden w-[78%] overflow-hidden rounded-[14px] border border-rule-strong bg-paper-raised shadow-lift md:block">
          <div className="flex items-center gap-3 border-b border-rule bg-paper px-4 py-2.5">
            <span aria-hidden className="flex gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-rule-strong" />
              <span className="h-2.5 w-2.5 rounded-full bg-rule-strong" />
              <span className="h-2.5 w-2.5 rounded-full bg-rule-strong" />
            </span>
            <span className="min-w-0 flex-1 truncate rounded-chip bg-paper-sunk px-3 py-1 text-center text-[13px] text-ink-faint" translate="no">
              oushodhsathi · /review
            </span>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element -- static screenshot, two theme variants */}
          <img src="/landing/review-light.webp" alt={reviewLabel} width={1200} height={699} className="only-light block h-auto w-full" />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/landing/review-dark.webp" alt={reviewLabel} width={1200} height={699} className="only-dark h-auto w-full" />
          <figcaption className="sr-only">{reviewLabel}</figcaption>
        </figure>

        {/* phone: the family's side, live */}
        {/* scaled down on wide screens so the whole phone stays on the cloth */}
        <figure className="relative mx-auto w-full max-w-[340px] md:absolute md:left-0 md:top-6 md:mx-0 md:w-[330px] md:origin-top-left md:scale-[0.8] lg:top-8 lg:scale-[0.84]">
          <div className="rounded-[44px] border border-rule-strong bg-ink p-[9px] shadow-lift">
            <div className="overflow-hidden rounded-[36px] bg-paper">
              <div aria-hidden className="mx-auto mt-2 h-[18px] w-[92px] rounded-chip bg-ink" />
              <div className="px-2.5 pb-4 pt-3">
                <HeroDemo replayLabel={replayLabel} />
              </div>
            </div>
          </div>
          <figcaption className="sr-only">{phoneLabel}</figcaption>
        </figure>
      </div>
    </div>
  );
}
