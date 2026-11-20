import type { Metadata, Viewport } from "next";
import { Anek_Bangla, Hind_Siliguri, Instrument_Sans, Schibsted_Grotesk } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";
import { MotionProvider } from "@/components/Motion";
import { RevealController } from "@/components/Reveal";
import { ServerWaking } from "@/components/ServerWaking";
import { motionArmScript } from "@/lib/motionPref";
import { revealArmScript } from "@/lib/reveal";
import { SITE_URL } from "@/lib/site";
import "./globals.css";

const hind = Hind_Siliguri({
  subsets: ["bengali", "latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-hind-siliguri",
  display: "swap",
  preload: false, // body text: 4 files (~160 KB); preloading them delayed first paint on slow phones
});
const anek = Anek_Bangla({
  subsets: ["bengali", "latin"],
  variable: "--font-anek-bangla",
  display: "swap",
});
const instrumentSans = Instrument_Sans({
  subsets: ["latin"],
  variable: "--font-instrument-sans",
  display: "swap",
  preload: false, // body text; only the display faces (the h1) are preloaded
});
const schibsted = Schibsted_Grotesk({
  subsets: ["latin"],
  style: ["normal", "italic"],
  variable: "--font-schibsted",
  display: "swap",
});

const description =
  "A pharmacist for every elderly home in Bangladesh: scan every medicine, catch duplicates and interactions, and a clinician confirms every finding before the family sees it.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: "OushodhSathi · ওষুধসাথী", template: "%s · OushodhSathi" },
  description,
  applicationName: "OushodhSathi",
  openGraph: {
    type: "website",
    siteName: "OushodhSathi · ওষুধসাথী",
    title: "OushodhSathi · ওষুধসাথী — Napa and Ace are the same medicine",
    description,
    locale: "bn_BD",
    alternateLocale: ["en_US"],
  },
  twitter: { card: "summary_large_image", title: "OushodhSathi · ওষুধসাথী", description },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f3f5f9" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0e1c" },
  ],
};

// Runs before paint: ?theme=light|dark (used for screenshots) or the saved choice.
const themeScript = `(function(){try{var q=new URLSearchParams(location.search).get('theme');var t=q||localStorage.getItem('theme');if(t==='light'||t==='dark'){document.documentElement.setAttribute('data-theme',t)}}catch(e){}})();`;

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const locale = await getLocale();
  const all = await getMessages();
  // Namespaces only server components read (getTranslations) stay on the server: about 11 KB less HTML on
  // every page. Client components read docs.live only (LivePanels); a test keeps this list honest.
  const { landing: _landing, legal: _legal, docs, ...rest } = all as Record<string, unknown> & { docs?: { live?: unknown } };
  void _landing; void _legal;
  const messages = { ...rest, docs: { live: docs?.live } } as typeof all;
  return (
    <html
      lang={locale}
      suppressHydrationWarning
      className={`${hind.variable} ${anek.variable} ${instrumentSans.variable} ${schibsted.variable}`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <script dangerouslySetInnerHTML={{ __html: revealArmScript }} />
        <script dangerouslySetInnerHTML={{ __html: motionArmScript }} />
      </head>
      <body>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <MotionProvider>{children}</MotionProvider>
          <RevealController />
          <ServerWaking />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
