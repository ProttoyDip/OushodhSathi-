import { ArrowRight, Stethoscope } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { LegalPage } from "@/components/LegalPage";

export const metadata: Metadata = {
  title: "For pharmacists and doctors",
  description: "Registered pharmacists and doctors confirm every OushodhSathi finding. How the review works and how to join the pilot.",
};

export default async function PharmacistsPage() {
  const t = await getTranslations("legal.pharmacists");
  const tl = await getTranslations("landing.footer");
  return (
    <LegalPage page="pharmacists">
      <div className="mt-10 flex flex-col gap-3 sm:flex-row">
        <Link href="/contact" className="press inline-flex min-h-14 items-center justify-center gap-2.5 rounded-card bg-neel px-6 text-lg font-semibold text-on-neel hover:bg-neel-hover">
          {t("cta")} <ArrowRight aria-hidden size={20} />
        </Link>
        <Link href="/review" className="press inline-flex min-h-14 items-center justify-center gap-2 rounded-card border border-rule-strong bg-paper-raised px-6 text-lg font-semibold text-ink hover:border-ink-faint">
          <Stethoscope aria-hidden size={20} /> {tl("reviewer")}
        </Link>
      </div>
    </LegalPage>
  );
}
