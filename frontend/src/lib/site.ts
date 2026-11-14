// Where the public pilot site sends people for the judge demo and the source code.
// The demo runs on its own deployment (its own API and database), so a demo reviewer login
// can never see a real family. Unset (local, or the demo site itself): links stay on this site.
const DEMO_SITE = (process.env.NEXT_PUBLIC_DEMO_SITE_URL || "").replace(/\/$/, "");

export const GITHUB_URL = "https://github.com/ProttoyDip/OushodhSathi-";

/** This site's public address: canonical links, the sitemap and social previews. */
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || "https://oushodhsathi.vercel.app").replace(/\/$/, "");

/** A path on the demo site, e.g. demoHref("/p/1"). */
export function demoHref(path: string): string {
  return `${DEMO_SITE}${path}`;
}
