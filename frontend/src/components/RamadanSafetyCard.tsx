import { ShieldAlert } from "lucide-react";

/**
 * Fixed clinician safety card for fasting with diabetes. Never generated, never reworded by AI.
 * Thresholds from the IDF-DAR Diabetes and Ramadan Practical Guidelines (2021): break the fast
 * below 3.9 mmol/L or above 16.7 mmol/L, or with symptoms of low sugar, high sugar,
 * dehydration or acute illness. Pending sign-off by the team's clinician.
 */
const POINTS: [string, string][] = [
  [
    "রক্তে শর্করা ৩.৯ mmol/L (৭০ mg/dL)-এর নিচে নামলে, বা কম শর্করার লক্ষণ দেখা দিলে: কাঁপুনি, ঘাম, বিভ্রান্তি, বুক ধড়ফড়।",
    "Blood sugar is below 3.9 mmol/L (70 mg/dL), or there are signs of low sugar: shaking, sweating, confusion, a racing heart.",
  ],
  [
    "রক্তে শর্করা ১৬.৭ mmol/L (৩০০ mg/dL)-এর ওপরে উঠলে, বা খুব বেশি শর্করা বা পানিশূন্যতার লক্ষণ দেখা দিলে: প্রচণ্ড তৃষ্ণা, মুখ শুকিয়ে যাওয়া, প্রস্রাব কমে যাওয়া, মাথা ঘোরা বা অজ্ঞান হয়ে যাওয়া।",
    "Blood sugar is above 16.7 mmol/L (300 mg/dL), or there are signs of very high sugar or dehydration: great thirst, a dry mouth, passing little urine, dizziness or fainting.",
  ],
  ["হঠাৎ খুব অসুস্থ লাগলে, বমি বা জ্বর হলে।", "Feeling suddenly very unwell, vomiting, or fever."],
];

export function RamadanSafetyCard() {
  return (
    <section aria-labelledby="ramadan-safety-h" className="break-inside-avoid rounded-card border-2 border-red bg-red-tint/50 p-5 print:border-ink print:bg-transparent">
      <h2 id="ramadan-safety-h" className="flex items-start gap-2 text-red print:text-ink">
        <ShieldAlert aria-hidden size={24} className="mt-0.5 shrink-0" />
        <span>
          <span lang="bn" className="block font-bn-display text-[22px] leading-tight">রোজা ভেঙে ফেলুন এবং ডাক্তারকে জানান, যদি —</span>
          <span lang="en" className="block text-base font-semibold">Break the fast and contact the doctor if:</span>
        </span>
      </h2>
      <ul className="mt-3 grid gap-3">
        {POINTS.map(([bn, en]) => (
          <li key={en} className="border-l-4 border-red pl-3 print:border-ink">
            <p lang="bn" className="text-ink">{bn}</p>
            <p lang="en" className="text-[15px] text-ink-soft">{en}</p>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-base text-ink">
        <span lang="bn">আঙুলে সুঁই ফুটিয়ে শর্করা মাপলে রোজা ভাঙে না।</span>{" "}
        <span lang="en" className="text-ink-soft">Checking blood sugar with a finger prick does not break the fast.</span>
      </p>
      <p className="mt-3 text-[13px] text-ink-faint">
        Fixed text, not written by AI, based on the IDF-DAR Diabetes and Ramadan Practical Guidelines (2021). Pending sign-off by the team&apos;s clinician.
      </p>
    </section>
  );
}
