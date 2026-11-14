import { ExternalLink, Mail, Phone } from "lucide-react";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { LegalPage } from "@/components/LegalPage";
import { GITHUB_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Contact",
  description: "Reach the OushodhSathi team about a lost family link, your data, or a problem with the app.",
};

// The team's address is configured per deployment; without one, GitHub is the channel.
const EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL || "";

export default async function ContactPage() {
  const t = await getTranslations("legal.contact");
  const button = "press inline-flex min-h-14 items-center justify-center gap-2.5 rounded-card px-6 text-lg font-semibold";
  return (
    <LegalPage page="contact">
      <div className="mt-8 flex flex-col gap-3 sm:flex-row">
        {EMAIL && (
          <a href={`mailto:${EMAIL}`} className={`${button} bg-neel text-on-neel hover:bg-neel-hover`}>
            <Mail aria-hidden size={20} /> {t("email")}
          </a>
        )}
        <a href={`${GITHUB_URL}/issues`} target="_blank" rel="noreferrer"
          className={`${button} border border-rule-strong bg-paper-raised text-ink hover:border-ink-faint`}>
          {t("github")} <ExternalLink aria-hidden size={18} />
        </a>
      </div>
      {!EMAIL && <p className="mt-3 text-[15px] text-ink-faint">{t("noEmail")}</p>}
      <p className="mt-10 flex items-start gap-3 rounded-card border border-red-line bg-red-tint p-4 text-[17px] text-red">
        <Phone aria-hidden size={20} className="mt-1 shrink-0" /> {t("medical")}
      </p>
    </LegalPage>
  );
}
