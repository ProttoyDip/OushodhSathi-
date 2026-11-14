import type { Metadata } from "next";

// A family's printed passport: private, never indexed.
export const metadata: Metadata = { robots: { index: false, follow: false } };

export default function PassportLayout({ children }: { children: React.ReactNode }) {
  return children;
}
