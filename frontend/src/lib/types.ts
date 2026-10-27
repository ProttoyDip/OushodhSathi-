export type Severity = "red" | "amber";
export type Slot = "morning" | "noon" | "night";
export type FlagCode =
  | "DUPLICATE_GENERIC"
  | "THERAPEUTIC_DUPLICATION"
  | "INTERACTION"
  | "BEERS_65"
  | "EXPIRED";
export type MatchMethod = "exact" | "fuzzy" | "web_unverified" | "not_found" | "manual";

export interface Patient {
  id: number;
  name: string;
  name_bn: string | null;
  age: number;
  district: string | null;
  conditions: string[];
  is_demo: boolean;
  created_at: string;
  last_checked_at: string | null;
  demo_label?: string | null;
}

export interface MedicineItem {
  id: number;
  patient_id: number;
  brand: string;
  strength: string | null;
  form: string | null;
  expiry: string | null;
  prescriber: string | null;
  source: string | null;
  confidence: number;
  schedule: Slot[];
  pills_left: number | null;
  doses_per_day: number | null;
  generic: string | null;
  drug_class: string | null;
  match_method: MatchMethod;
  match_score: number | null;
  match_source: string | null;
  prompt_version: string | null;
  model_id: string | null;
  confirmed: boolean;
  needs_review: boolean;
  thumbnail?: string | null;
}

export interface Flag {
  id: number;
  patient_id: number;
  key: string;
  code: FlagCode;
  severity: Severity;
  item_ids: number[];
  evidence: string;
  routed_to: "doctor" | "pharmacist";
  data_source: string;
  meta: Record<string, unknown>;
  status: "pending_review" | "confirmed" | "dismissed";
  active: boolean;
  created_at: string;
  reviewer: string | null;
  note: string | null;
  reviewed_at: string | null;
  explanation_bn: string | null;
  items: MedicineItem[];
  patient?: { id: number; name: string; name_bn: string | null; age: number; is_demo: boolean } | null;
}

export interface FamilyStatus {
  review_state: "not_checked" | "in_review" | "reviewed";
  last_checked_at: string | null;
  confirmed_flags: number;
  items_confirmed: number;
}

export interface PassportEntry {
  id: number;
  generic: string | null;
  brand: string;
  strength: string | null;
  prescriber: string | null;
  needs_review: boolean;
}

export interface Passport {
  patient: { id: number; name: string; name_bn: string | null; age: number; conditions: string[]; district: string | null };
  groups: Record<Slot | "as_needed", PassportEntry[]>;
  confirmed_notes: {
    code: FlagCode;
    severity: Severity;
    brands: string[];
    note: string | null;
    explanation_bn: string | null;
    reviewer: string | null;
    reviewed_at: string | null;
  }[];
  medicine_count: number;
  generated_at: string;
  demo_label: string | null;
}

export interface Report {
  patient: { id: number; name: string; name_bn: string | null; age: number };
  bp: { readings: { taken_on: string; systolic: number; diastolic: number }[]; target: { systolic: number; diastolic: number } };
  doses: { scheduled: number; taken: number; is_demo: boolean; label: string } | null;
  flags: { confirmed_open: number; resolved: number; reviewed: number };
  refills_due: { brand: string; generic: string | null; pills_left: number; days_left: number }[];
  demo_label: string | null;
}

export interface ReviewQueue {
  flags: Flag[];
  counts: { pending: number; red: number; amber: number; doctor: number; pharmacist: number };
}

export interface AuditEntry {
  id: number;
  flag_id: number;
  status: "confirmed" | "dismissed" | "undone";
  reviewer: string;
  note: string | null;
  created_at: string;
  code: FlagCode;
  severity: Severity;
  evidence: string;
}

export interface Health {
  status: string;
  demo_mode: boolean;
  providers: Record<"vision" | "text" | "explain_bn", string[]>;
  models: { vision: string; text: string; explain_bn_local: string | null };
  ollama_reachable: boolean;
  web_lookup: { tavily: boolean; perplexity: boolean };
  prompts: Record<string, string>;
  reviewer_login: string;
  test_count: number;
  patients: number;
}

export interface EvalResult {
  prompt_version: string;
  model_id: string | null;
  run_at: string;
  images: number;
  labelled_items: number;
  brand_accuracy: number;
  strength_accuracy: number;
  avg_confidence: number | null;
  brand_accuracy_ci?: [number, number];
  strength_accuracy_ci?: [number, number];
}

export interface Proportion {
  label: string;
  k: number;
  n: number;
  p: number;
  ci_low: number;
  ci_high: number;
}

export interface PilotStats {
  households: number;
  medicines?: number;
  proportions: Proportion[];
}

export interface ModelRef {
  provider: string;
  model: string;
}

export interface ModelTask {
  chain: ModelRef[];
  preferred: ModelRef | null;
  last_used: (ModelRef & { at: number; cached?: boolean }) | null;
  choosable: boolean;
}

export interface ModelsInfo {
  tasks: Record<"vision" | "text" | "explain_bn" | "sathi", ModelTask>;
  demo_mode: boolean;
}

export type StepCode =
  | "EMERGENCY_ACTIVE" | "PHARMACIST_REPLIED" | "RESULTS_READY" | "LOW_CONFIDENCE" | "ITEMS_TO_CONFIRM" | "NO_SCAN"
  | "READY_TO_SEND" | "SENT_FOR_REVIEW" | "PASSPORT_NOT_SAVED" | "REFILL_DUE" | "ALL_GOOD";

export interface NextStep {
  code: StepCode;
  params: Record<string, string | number>;
  text: string;
  button: string;
  route: string;
  phrased_by: string;
}

export interface SathiAction {
  label: string;
  route: string | null;
  tel: string | null;
  question_draft: string | null;
}

export interface SathiReply {
  kind: "answer" | "not_in_guide" | "medical_redirect" | "emergency";
  text: string;
  guide_ids: string[];
  actions: SathiAction[];
  source: string;
}

export interface Question {
  id: number;
  patient_id: number;
  text: string;
  created_at: string;
  reply: string | null;
  replied_by: string | null;
  replied_at: string | null;
  reply_seen_at: string | null;
  patient?: { id: number; name: string; name_bn: string | null; age: number; is_demo: boolean } | null;
}
