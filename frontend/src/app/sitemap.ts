import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

const PUBLIC_PAGES = ["", "/docs", "/for-pharmacists", "/privacy", "/terms", "/contact"];

export default function sitemap(): MetadataRoute.Sitemap {
  return PUBLIC_PAGES.map((path) => ({
    url: `${SITE_URL}${path}`,
    changeFrequency: path === "" ? "weekly" : "monthly",
    priority: path === "" ? 1 : 0.6,
  }));
}
