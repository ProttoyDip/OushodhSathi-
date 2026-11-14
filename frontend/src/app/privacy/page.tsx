import type { Metadata } from "next";
import { LegalPage } from "@/components/LegalPage";

export const metadata: Metadata = {
  title: "Privacy notice",
  description: "What OushodhSathi keeps, who can see it, and how a family downloads or deletes it.",
};

export default function PrivacyPage() {
  return <LegalPage page="privacy" />;
}
