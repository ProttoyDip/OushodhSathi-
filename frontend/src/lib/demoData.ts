// Invented demo household (mirrors backend/app/demo.py). Always shown with the
// "Demo household — invented data" tag. Used by /styleguide, the landing hero and /demo.
import type { Flag, MatchMethod, MedicineItem, Passport, Slot } from "./types";

const base = {
  patient_id: 1, form: "tablet", source: "strip", pills_left: null, doses_per_day: null,
  match_score: 100, match_source: "brands_seed.csv", prompt_version: "demo", model_id: "demo",
  confirmed: true, needs_review: false, schedule: [] as Slot[], match_method: "exact" as MatchMethod,
};

export const DEMO_ITEMS: Record<string, MedicineItem> = {
  napa: { ...base, id: 1, brand: "Napa", purpose: "Pain or fever", purpose_bn: "ব্যথা বা জ্বর", strength: "500 mg", expiry: "2027-03", prescriber: "Local drug shop", confidence: 0.96, generic: "paracetamol", drug_class: "analgesic-paracetamol", schedule: ["morning", "night"] },
  ace: { ...base, id: 2, brand: "Ace", purpose: "Pain or fever", purpose_bn: "ব্যথা বা জ্বর", strength: "500 mg", expiry: "2026-12", prescriber: "Village doctor", confidence: 0.91, generic: "paracetamol", drug_class: "analgesic-paracetamol", schedule: ["noon"] },
  camlodin: { ...base, id: 3, brand: "Camlodin", purpose: "Blood pressure", purpose_bn: "রক্তচাপ", strength: "5 mg", expiry: "2027-06", prescriber: "Dr. A (Cumilla Medical College OPD)", confidence: 0.97, generic: "amlodipine", drug_class: "CCB-dihydropyridine", source: "box", schedule: ["morning"] },
  amdocal: { ...base, id: 4, brand: "Amdocal", purpose: "Blood pressure", purpose_bn: "রক্তচাপ", strength: "5 mg", expiry: "2027-01", prescriber: "Village doctor", confidence: 0.82, generic: "amlodipine", drug_class: "CCB-dihydropyridine", schedule: ["night"] },
  tryptin: { ...base, id: 8, brand: "Tryptin", strength: "10 mg", expiry: "2026-09", prescriber: "Village doctor", confidence: 0.68, generic: "amitriptyline", drug_class: "TCA", needs_review: true, confirmed: false, schedule: ["night"] },
  unknown: { ...base, id: 20, brand: "Napa Extra", strength: "500 mg", expiry: "2027-04", prescriber: null, confidence: 0.88, generic: null, drug_class: null, match_method: "not_found", match_score: null, match_source: null, needs_review: true, confirmed: false },
  web: { ...base, id: 21, brand: "Bisocor", strength: "2.5 mg", expiry: "2027-02", prescriber: "Dr. A (Cumilla Medical College OPD)", confidence: 0.9, generic: "bisoprolol", drug_class: null, match_method: "web_unverified", match_score: null, match_source: "https://medex.com.bd/", needs_review: true, confirmed: false },
};

export const DEMO_FLAG: Flag = {
  id: 1, patient_id: 1, key: "demo", code: "DUPLICATE_GENERIC", severity: "red", item_ids: [1, 2],
  evidence: "Napa 500 mg and Ace 500 mg (from Local drug shop, Village doctor) both contain paracetamol. The patient may be taking a double dose.",
  routed_to: "doctor", data_source: "brand table", meta: { generic: "paracetamol" }, status: "confirmed", active: true,
  created_at: "2026-10-26T08:00:00+00:00", reviewer: "Demo pharmacist (invented)",
  note: "Both strips are paracetamol. Please bring both strips to the next visit so we can decide together.",
  reviewed_at: "2026-10-26T09:10:00+00:00",
  explanation_bn:
    "Napa ও Ace — নাম আলাদা হলেও দুটোই আসলে একই ওষুধ: প্যারাসিটামল। একসাথে খেলে একই ওষুধ দুইবার খাওয়া হতে পারে। ডাক্তার বিষয়টি দেখেছেন। ডাক্তারের সাথে কথা না বলে কোনো ওষুধ বন্ধ বা পরিবর্তন করবেন না।",
  items: [DEMO_ITEMS.napa, DEMO_ITEMS.ace],
  patient: { id: 1, name: "Rahima Begum", name_bn: "রহিমা বেগম", age: 68, is_demo: true },
};

export const DEMO_PENDING_FLAGS: Flag[] = [
  { ...DEMO_FLAG, id: 11, status: "pending_review", created_at: "2026-10-26T06:46:00+00:00" },
  {
    ...DEMO_FLAG, id: 12, code: "INTERACTION", severity: "amber", routed_to: "pharmacist", status: "pending_review",
    created_at: "2026-10-26T08:08:00+00:00",
    items: [{ ...DEMO_ITEMS.camlodin, id: 5, brand: "Angilock", strength: "50 mg", generic: "losartan" }, { ...DEMO_ITEMS.napa, id: 6, brand: "Clofenac", strength: "50 mg", generic: "diclofenac" }],
  },
];

export const DEMO_BP = [
  [168, 98], [164, 96], [159, 94], [162, 97], [150, 92], [146, 90], [142, 88],
].map(([systolic, diastolic], i) => ({
  taken_on: `2026-10-${20 + i}`,
  systolic,
  diastolic,
}));

export const DEMO_PASSPORT: Passport = {
  patient: { id: 1, name: "Rahima Begum", name_bn: "রহিমা বেগম", age: 68, conditions: ["hypertension", "type 2 diabetes"], district: "Cumilla" },
  groups: {
    morning: [
      { id: 1, generic: "paracetamol", brand: "Napa", purpose: "Pain or fever", purpose_bn: "ব্যথা বা জ্বর", strength: "500 mg", prescriber: "Local drug shop", needs_review: false },
      { id: 3, generic: "amlodipine", brand: "Camlodin", purpose: "Blood pressure", purpose_bn: "রক্তচাপ", strength: "5 mg", prescriber: "Dr. A", needs_review: false },
      { id: 9, generic: "metformin", brand: "Comet", purpose: "Diabetes", purpose_bn: "ডায়াবেটিস", strength: "500 mg", prescriber: "Dr. A", needs_review: false },
    ],
    noon: [{ id: 2, generic: "paracetamol", brand: "Ace", purpose: "Pain or fever", purpose_bn: "ব্যথা বা জ্বর", strength: "500 mg", prescriber: "Village doctor", needs_review: false }],
    night: [
      { id: 4, generic: "amlodipine", brand: "Amdocal", purpose: "Blood pressure", purpose_bn: "রক্তচাপ", strength: "5 mg", prescriber: "Village doctor", needs_review: false },
      { id: 9, generic: "metformin", brand: "Comet", purpose: "Diabetes", purpose_bn: "ডায়াবেটিস", strength: "500 mg", prescriber: "Dr. A", needs_review: false },
    ],
    as_needed: [],
  },
  confirmed_notes: [
    { code: "DUPLICATE_GENERIC", severity: "red", brands: ["Napa", "Ace"], note: DEMO_FLAG.note, explanation_bn: DEMO_FLAG.explanation_bn, reviewer: DEMO_FLAG.reviewer, reviewed_at: DEMO_FLAG.reviewed_at },
  ],
  medicine_count: 6,
  generated_at: "2026-10-26T09:12:00+00:00",
  demo_label: "Demo household — invented data",
  allergies: ["Penicillin"],
  allergies_confirmed_by: "Demo pharmacist (invented)",
  allergies_confirmed_at: "2026-10-26T09:10:00+00:00",
  prescribers: [
    { name: "Dr. A", medicines: ["Camlodin", "Comet"] },
    { name: "Village doctor", medicines: ["Ace", "Amdocal"] },
    { name: "Local drug shop", medicines: ["Napa"] },
  ],
  last_reviewed: { by: "Demo pharmacist (invented)", role: "pharmacist", at: "2026-10-26T09:10:00+00:00" },
  emergency_enabled: true,
};
