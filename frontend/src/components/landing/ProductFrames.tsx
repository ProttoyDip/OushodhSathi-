import { HeroDemo } from "@/components/landing/HeroDemo";

/**
 * The hero object: the family's side of the product, live, on the one indigo-dyed cloth panel of
 * the page. Real StripCards assemble, then Napa and Ace travel together under "দুটোই প্যারাসিটামল".
 * No drawn phone or browser frame: the content stands on the cloth by itself.
 */
export function ProductFrames({ replayLabel, phoneLabel }: { replayLabel: string; phoneLabel: string }) {
  return (
    <figure className="dyed-cloth px-5 py-8 sm:px-10 sm:py-12">
      <HeroDemo replayLabel={replayLabel} />
      <figcaption className="sr-only">{phoneLabel}</figcaption>
    </figure>
  );
}

/** The pharmacist's side: a real screenshot of /review (light and dark), framed by a hairline only. */
export function ReviewScreenshot({ label }: { label: string }) {
  return (
    <figure className="min-w-0">
      <div className="overflow-hidden rounded-card border border-rule-strong bg-paper shadow-soft">
        {/* eslint-disable-next-line @next/next/no-img-element -- static screenshot, two theme variants */}
        <img src="/landing/review-light.webp" alt={label} width={1200} height={699} loading="lazy" className="only-light block h-auto w-full" />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/landing/review-dark.webp" alt={label} width={1200} height={699} loading="lazy" className="only-dark h-auto w-full" />
      </div>
      <figcaption className="mt-3 text-[15px] text-ink-faint">{label}</figcaption>
    </figure>
  );
}
