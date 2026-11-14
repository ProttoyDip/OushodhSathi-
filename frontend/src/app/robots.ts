import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

// Family lists, passports, emergency pages and the clinician tools are private: never indexed.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/p/", "/passport/", "/e/", "/review", "/admin", "/start", "/models"] },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
