"use client";

import { ArrowLeft, FlaskConical, Monitor, Moon, Sun } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState, useTransition } from "react";
import { cx } from "@/lib/format";
import { Wordmark } from "./BrandMark";

export function LangToggle({ className }: { className?: string }) {
  const t = useTranslations("common");
  const locale = useLocale();
  const router = useRouter();
  const [pending, start] = useTransition();
  return (
    <button
      type="button"
      lang={locale === "bn" ? "en" : "bn"}
      aria-label={t("langSwitchLabel")}
      disabled={pending}
      onClick={() => {
        document.cookie = `locale=${locale === "bn" ? "en" : "bn"}; path=/; max-age=31536000; samesite=lax`;
        start(() => router.refresh());
      }}
      className={cx(
        "press inline-flex h-12 min-w-12 items-center justify-center rounded-chip border border-rule bg-paper-raised px-4 text-base font-medium text-ink transition-colors hover:border-rule-strong disabled:opacity-60",
        className,
      )}
    >
      {t("langSwitch")}
    </button>
  );
}

type Mode = "system" | "light" | "dark";

export function ThemeToggle({ className }: { className?: string }) {
  const t = useTranslations("common");
  const [mode, setMode] = useState<Mode>("system");
  useEffect(() => {
    const saved = document.documentElement.getAttribute("data-theme");
    if (saved === "light" || saved === "dark") setMode(saved);
  }, []);
  const next: Record<Mode, Mode> = { system: "light", light: "dark", dark: "system" };
  const Icon = mode === "light" ? Sun : mode === "dark" ? Moon : Monitor;
  const label = { system: t("themeSystem"), light: t("themeLight"), dark: t("themeDark") }[mode];
  return (
    <button
      type="button"
      aria-label={t("themeLabel", { mode: label })}
      title={t("themeLabel", { mode: label })}
      onClick={() => {
        const m = next[mode];
        setMode(m);
        try {
          if (m === "system") {
            document.documentElement.removeAttribute("data-theme");
            localStorage.removeItem("theme");
          } else {
            document.documentElement.setAttribute("data-theme", m);
            localStorage.setItem("theme", m);
          }
        } catch {}
      }}
      className={cx(
        "press inline-flex h-12 w-12 items-center justify-center rounded-chip border border-rule bg-paper-raised text-ink transition-colors hover:border-rule-strong",
        className,
      )}
    >
      <Icon aria-hidden size={20} />
    </button>
  );
}

export function DemoTag({ label, className }: { label?: string; className?: string }) {
  const t = useTranslations("common");
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 rounded-chip border border-dashed border-rule-strong px-3 py-1 text-[13px] font-medium text-ink-soft",
        className,
      )}
    >
      <FlaskConical aria-hidden size={14} />
      {label ?? t("demoTag")}
    </span>
  );
}

/** Family app width: a phone column, widening to a working desktop canvas from lg up. */
export const familyWidth = "max-w-[480px] lg:max-w-[1120px] lg:px-8";

/** Top bar for the family app: wordmark, optional back link, language + theme. */
export function FamilyHeader({ back, demo }: { back?: string; demo?: boolean }) {
  const t = useTranslations("common");
  return (
    <header className={`no-print mx-auto w-full px-4 pt-3 ${familyWidth}`}>
      <div className="flex items-center justify-between gap-2">
        {back ? (
          <Link
            href={back}
            className="-ml-2 inline-flex h-12 items-center gap-1.5 rounded-chip px-2 text-base font-medium text-ink"
          >
            <ArrowLeft aria-hidden size={22} />
            {t("back")}
          </Link>
        ) : (
          <Link href="/" className="inline-flex h-12 items-center rounded-md" title={t("home")}>
            <Wordmark compact />
          </Link>
        )}
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <LangToggle />
        </div>
      </div>
      {demo && <DemoTag className="mt-2" />}
    </header>
  );
}

export const buttonStyles = {
  primary:
    "press inline-flex min-h-14 w-full items-center justify-center gap-2.5 rounded-card bg-neel px-6 text-lg font-semibold text-on-neel shadow-soft transition-colors duration-150 hover:bg-neel-hover disabled:cursor-not-allowed disabled:opacity-50",
  secondary:
    "press inline-flex min-h-12 items-center justify-center gap-2 rounded-card border border-rule-strong bg-paper-raised px-5 text-base font-semibold text-ink transition-colors duration-150 hover:border-ink-faint disabled:opacity-50",
  quiet:
    "press inline-flex min-h-12 items-center justify-center gap-2 rounded-card px-4 text-base font-medium text-ink-soft underline-offset-4 hover:text-ink hover:underline disabled:opacity-50",
};
