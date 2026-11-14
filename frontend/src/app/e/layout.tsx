import type { Metadata } from "next";

// The emergency page behind the passport QR: reachable by its secret link only, never indexed.
export const metadata: Metadata = { robots: { index: false, follow: false } };

export default function EmergencyLayout({ children }: { children: React.ReactNode }) {
  return children;
}
