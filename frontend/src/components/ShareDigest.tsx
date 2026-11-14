"use client";

import { Check, Copy, MessageCircle } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { buttonStyles } from "@/components/Chrome";
import { api } from "@/lib/api";
import { cx, num } from "@/lib/format";

/** A Bangla + English summary for the family WhatsApp group. It carries the read-only emergency
 * link, never the private family link, and counts rather than medicine details. */
async function buildDigest(pid: number): Promise<string> {
  const [passport, today, savings, emergency] = await Promise.all([
    api.passport(pid), api.today(pid), api.savings(pid).catch(() => null), api.emergencyToken(pid).catch(() => ({ token: null })),
  ]);
  const p = passport.patient;
  const findings = passport.confirmed_notes.length;
  const [m, n, k] = (["morning", "noon", "night"] as const).map((s) => today.slots[s].length);
  const yearly = savings?.total_yearly_bdt ?? 0;
  const link = emergency.token ? `${window.location.origin}/e/${emergency.token}` : null;
  const bn = (x: number) => num(x, "bn");
  const lines = [
    `ওষুধসাথী · ${p.name_bn ?? p.name} (${bn(p.age)})`,
    `• ফার্মাসিস্ট বা ডাক্তারের নিশ্চিত করা বিষয়: ${bn(findings)}টি`,
    `• অনুমোদিত সময়সূচি: সকালে ${bn(m)}টি, দুপুরে ${bn(n)}টি, রাতে ${bn(k)}টি ওষুধ`,
    ...(yearly > 0 ? [`• একই জেনেরিকের কম দামের ব্র্যান্ডে বছরে প্রায় ৳${bn(yearly)} কম লাগতে পারে — ফার্মাসিস্টকে জিজ্ঞেস করুন`] : []),
    link ? `• জরুরি পাসপোর্ট (শুধু পড়া যায়): ${link}` : "• জরুরি পাতা এখনো চালু করা হয়নি",
    "",
    `OushodhSathi · ${p.name} (${p.age})`,
    `• Findings confirmed by the pharmacist or doctor: ${findings}`,
    `• Approved schedule: ${m} in the morning, ${n} at noon, ${k} at night`,
    ...(yearly > 0 ? [`• Same-medicine, lower-price brands could save about ৳${yearly} a year — ask the pharmacist`] : []),
    link ? `• Emergency passport (read-only): ${link}` : "• Emergency page not switched on yet",
  ];
  if (passport.demo_label) lines.push("", passport.demo_label);
  return lines.join("\n");
}

export function ShareDigest({ pid, className }: { pid: number; className?: string }) {
  const t = useTranslations("digest");
  const [state, setState] = useState<"idle" | "busy" | "copied" | "error">("idle");

  async function share(how: "whatsapp" | "copy") {
    setState("busy");
    try {
      const text = await buildDigest(pid);
      if (how === "whatsapp") {
        window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank", "noopener");
        setState("idle");
      } else {
        await navigator.clipboard.writeText(text);
        setState("copied");
        setTimeout(() => setState("idle"), 3000);
      }
    } catch {
      setState("error");
    }
  }

  return (
    <section aria-labelledby="digest-h" className={cx("rounded-card border border-rule bg-paper-raised p-5", className)}>
      <h2 id="digest-h" className="font-semibold">{t("title")}</h2>
      <p className="mt-1 text-base text-ink-soft">{t("body")}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" disabled={state === "busy"} onClick={() => share("whatsapp")} className={buttonStyles.secondary}>
          <MessageCircle aria-hidden size={18} /> {t("whatsapp")}
        </button>
        <button type="button" disabled={state === "busy"} onClick={() => share("copy")} className={buttonStyles.quiet}>
          {state === "copied" ? <Check aria-hidden size={18} className="text-green" /> : <Copy aria-hidden size={18} />}
          {state === "copied" ? t("copied") : t("copy")}
        </button>
      </div>
      {state === "error" && <p role="alert" className="mt-2 text-[15px] text-red">{t("failed")}</p>}
    </section>
  );
}
