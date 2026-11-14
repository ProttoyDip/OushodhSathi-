import type { Metadata } from "next";

// Clinician and team tools: never indexed.
export const metadata: Metadata = { robots: { index: false, follow: false } };

// The reviewer dashboard follows the site language toggle (Bangla or English).
export default function ReviewLayout({ children }: { children: React.ReactNode }) {
  return <div className="min-h-dvh text-[15px]">{children}</div>;
}
