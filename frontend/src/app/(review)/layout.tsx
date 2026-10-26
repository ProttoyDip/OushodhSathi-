import { NextIntlClientProvider } from "next-intl";
import en from "../../../messages/en.json";

// The reviewer dashboard is an English clinical tool; family-facing Bangla is previewed inside it.
export default function ReviewLayout({ children }: { children: React.ReactNode }) {
  return (
    <NextIntlClientProvider locale="en" messages={en} timeZone="Asia/Dhaka">
      <div lang="en" className="min-h-dvh text-[15px]">{children}</div>
    </NextIntlClientProvider>
  );
}
