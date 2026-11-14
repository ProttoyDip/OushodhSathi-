"use client";

import bn from "../../messages/bn.json";
import en from "../../messages/en.json";
import "./globals.css";

/** The root layout itself failed, so no providers are available: both languages, from the locale files. */
export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="bn">
      <body className="bg-paper text-ink">
        <main className="mx-auto flex min-h-dvh max-w-[560px] flex-col justify-center gap-6 px-6 py-16">
          {[bn, en].map((m) => (
            <section key={m.errors.errorTitle} lang={m === bn ? "bn" : "en"}>
              <h1 className="text-[30px] font-semibold leading-tight">{m.errors.errorTitle}</h1>
              <p className="mt-2 text-lg text-ink-soft">{m.errors.errorBody}</p>
            </section>
          ))}
          <button type="button" onClick={reset} className="min-h-14 w-fit rounded-[10px] bg-neel px-6 text-lg font-semibold text-on-neel">
            {bn.errors.retry} · {en.errors.retry}
          </button>
        </main>
      </body>
    </html>
  );
}
