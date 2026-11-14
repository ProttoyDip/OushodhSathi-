import { Home } from "lucide-react";
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Wordmark } from "@/components/BrandMark";

export default async function NotFound() {
  const t = await getTranslations("errors");
  return (
    <main className="mx-auto flex min-h-dvh max-w-[560px] flex-col justify-center px-6 py-16">
      <Link href="/" className="w-fit"><Wordmark /></Link>
      <p aria-hidden className="mt-10 font-display text-[72px] leading-none text-stitch">404</p>
      <h1 className="mt-4 font-display text-[36px] leading-[1.1] text-ink">{t("notFoundTitle")}</h1>
      <p className="mt-3 text-lg text-ink-soft">{t("notFoundBody")}</p>
      <Link href="/" className="press mt-8 inline-flex min-h-14 w-fit items-center gap-2.5 rounded-card bg-neel px-6 text-lg font-semibold text-on-neel hover:bg-neel-hover">
        <Home aria-hidden size={20} /> {t("home")}
      </Link>
    </main>
  );
}
