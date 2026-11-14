import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Wordmark } from "@/components/BrandMark";
import { LangToggle, ThemeToggle } from "@/components/Chrome";
import { stickyBar } from "@/lib/layout";
import { Analytics } from "@vercel/analytics/next";

type Section = { h: string; p: string[] };
const PAGES = [["/privacy", "privacy"], ["/terms", "terms"], ["/contact", "contact"], ["/for-pharmacists", "pharmacists"]] as const;

/** Privacy, terms, contact and the pharmacist page: one quiet, readable column in both languages. */
export async function LegalPage({ page, children }: {
  page: "privacy" | "terms" | "contact" | "pharmacists";
  children?: React.ReactNode;
}) {
  const t = await getTranslations("legal");
  const sections = t.has(`${page}.sections`) ? (t.raw(`${page}.sections`) as Section[]) : [];

  return (
    <div className="min-h-dvh">
      <Analytics />
      <div className={stickyBar}>
        <nav aria-label="Main" className="mx-auto flex max-w-[1200px] items-center justify-between gap-3 px-5 py-3 sm:px-8">
          <Link href="/" className="inline-flex h-11 items-center gap-2 rounded-chip pr-2 text-[15px] font-medium text-ink-soft hover:text-ink">
            <ArrowLeft aria-hidden size={18} /> <span className="sr-only">{t("back")}</span> <Wordmark />
          </Link>
          <div className="flex items-center gap-2">
            <ThemeToggle className="h-11 w-11" />
            <LangToggle className="h-11" />
          </div>
        </nav>
      </div>
      <main className="mx-auto max-w-[760px] px-5 pb-20 pt-10 sm:px-8 lg:pt-16">
        <h1 className="font-display text-[clamp(36px,5vw,56px)] leading-[1.05] text-ink">{t(`${page}.title`)}</h1>
        {page !== "contact" && <p className="mt-3 text-[15px] text-ink-faint">{t("updated")}</p>}
        <span aria-hidden className="stitch-x mt-6 block w-24" />
        <p className="mt-6 text-lg leading-relaxed text-ink-soft">{t(`${page}.intro`)}</p>
        {sections.map((s) => (
          <section key={s.h} className="mt-10">
            <h2 className="text-[24px] font-semibold leading-tight text-ink">{s.h}</h2>
            {s.p.map((para) => (
              <p key={para.slice(0, 40)} className="mt-3 text-[18px] leading-relaxed text-ink-soft">{para}</p>
            ))}
          </section>
        ))}
        {children}
        <nav aria-label={t("other")} className="mt-16 border-t border-rule pt-6">
          <p className="text-[14px] font-semibold uppercase tracking-[0.08em] text-ink-faint">{t("other")}</p>
          <ul className="mt-2 flex flex-wrap gap-x-6 gap-y-1">
            {PAGES.filter(([, k]) => k !== page).map(([href, k]) => (
              <li key={href}>
                <Link href={href} className="inline-flex min-h-11 items-center text-[17px] text-neel underline-offset-4 hover:underline">
                  {t(`${k}.title`)}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </main>
    </div>
  );
}
