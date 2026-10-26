import { getRequestConfig } from "next-intl/server";
import { cookies } from "next/headers";

export const LOCALES = ["bn", "en"] as const;
export type Locale = (typeof LOCALES)[number];

// Bangla first. The language toggle writes the `locale` cookie.
export default getRequestConfig(async () => {
  const store = await cookies();
  const locale: Locale = store.get("locale")?.value === "en" ? "en" : "bn";
  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
    timeZone: "Asia/Dhaka",
  };
});
