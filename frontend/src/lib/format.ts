// Locale-aware formatting. Bangla screens use Bangla numerals; medicine strengths are
// shown exactly as printed on the strip (Latin), because that is what the family sees.

const GENERIC_BN: Record<string, string> = {
  paracetamol: "প্যারাসিটামল",
  amlodipine: "অ্যামলোডিপিন",
  losartan: "লোসারটান",
  diclofenac: "ডাইক্লোফেনাক",
  clonazepam: "ক্লোনাজেপাম",
  amitriptyline: "অ্যামিট্রিপটিলিন",
  metformin: "মেটফরমিন",
  omeprazole: "ওমিপ্রাজল",
  esomeprazole: "ইসোমিপ্রাজল",
  naproxen: "ন্যাপ্রোক্সেন",
  aceclofenac: "অ্যাসিক্লোফেনাক",
  aspirin: "অ্যাসপিরিন",
  atorvastatin: "অ্যাটরভাস্টাটিন",
  glibenclamide: "গ্লিবেনক্লামাইড",
};

export function genericName(generic: string | null | undefined, locale: string): string {
  if (!generic) return "";
  if (locale !== "bn") return generic.replace(/\b\w/g, (c) => c.toUpperCase());
  return generic
    .split("+")
    .map((g) => GENERIC_BN[g.trim().toLowerCase()] ?? g.trim())
    .join(" + ");
}

export function num(n: number, locale: string, digits = 0): string {
  return new Intl.NumberFormat(locale === "bn" ? "bn-BD" : "en-GB", {
    maximumFractionDigits: digits,
  }).format(n);
}

export function date(iso: string | null | undefined, locale: string, opts?: Intl.DateTimeFormatOptions): string {
  if (!iso) return "";
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  return new Intl.DateTimeFormat(locale === "bn" ? "bn-BD" : "en-GB", opts ?? { day: "numeric", month: "long", year: "numeric" }).format(d);
}

/** "2027-03" -> "03/2027" (as printed on strips) */
export function expiry(ym: string | null | undefined, locale: string): string {
  if (!ym) return "";
  const [y, m] = ym.split("-");
  const s = `${m}/${y}`;
  return locale === "bn" ? s.replace(/\d/g, (d) => "০১২৩৪৫৬৭৮৯"[Number(d)]) : s;
}

export function since(iso: string, now = Date.now()): string {
  const mins = Math.max(0, Math.round((now - new Date(iso).getTime()) / 60000));
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 48) return `${hours}h ${mins % 60}m`;
  return `${Math.floor(hours / 24)}d`;
}

export function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}
