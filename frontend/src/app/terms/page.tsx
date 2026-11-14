import type { Metadata } from "next";
import { LegalPage } from "@/components/LegalPage";

export const metadata: Metadata = {
  title: "Terms of use",
  description: "The terms of the OushodhSathi pilot: what the service is, and what it never does.",
};

export default function TermsPage() {
  return <LegalPage page="terms" />;
}
