import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { FamilyKeyFromUrl } from "@/components/FamilyKeyFromUrl";
import { Sathi } from "@/components/sathi/Sathi";

// A family's list is private: never indexed, never in a search result.
export const metadata: Metadata = { robots: { index: false, follow: false } };

export default async function FamilyLayout({ children }: { children: React.ReactNode }) {
  const t = await getTranslations("landing.footer");
  // Elder-friendly floor: 18px body text everywhere in the family app.
  return (
    <div className="min-h-dvh text-[18px] leading-relaxed">
      <FamilyKeyFromUrl />
      {children}
      <p className="mx-auto max-w-[720px] px-4 pt-10 text-center text-[15px] leading-relaxed text-ink-faint print:hidden">
        {t("family")}
      </p>
      {/* room so the end of every page can scroll clear of Sathi's button */}
      <div aria-hidden className="h-20" />
      <Sathi />
    </div>
  );
}
