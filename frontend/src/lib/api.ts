import type {
  AuditEntry, BPPhotoReading, BPTrend, CaseSummary, CleanupItem, EmergencyPage, EvalResult, FamilyStatus, Flag, Health, MedicineItem,
  ActivityEntry, ModelsInfo, NextStep, Passport, Patient, PilotStats, Question, RamadanRequest, Report, ReviewQueue,
  AdherenceSummary, DoseTick, KidneyView, ReviewerAccount, Slot, ReviewerInvite, SathiReply, Savings, Today, VisitPrep,
} from "./types";
import { familyKey } from "./familyKey";

// A production build on Vercel without NEXT_PUBLIC_API_URL would quietly call localhost from every phone.
const configuredApi = process.env.NEXT_PUBLIC_API_URL;
if (!configuredApi && process.env.NODE_ENV === "production" && process.env.VERCEL) {
  throw new Error("NEXT_PUBLIC_API_URL must be set for a production build");
}
export const API_URL = (configuredApi || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit & { token?: string; pid?: number; admin?: string } = {}): Promise<T> {
  const { token, pid, admin, headers, ...rest } = init;
  const key = pid !== undefined ? familyKey(pid) : null;
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...rest,
      headers: {
        ...(rest.body && !(rest.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
        ...(token ? { "X-Reviewer-Token": token } : {}),
        ...(key ? { "X-Family-Key": key } : {}),
        ...(admin ? { "X-Admin-Token": admin } : {}),
        ...headers,
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "offline");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new ApiError(res.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

const json = (body: unknown) => JSON.stringify(body);

export const api = {
  health: () => request<Health>("/health"),
  evalResults: () => request<EvalResult[]>("/eval/results"),
  pilotStats: () => request<PilotStats>("/pilot/stats"),
  models: () => request<ModelsInfo>("/models"),
  // changes the model for everyone: reviewers only
  setModel: (token: string, kind: "vision" | "text", choice: { provider: string; model: string } | null) =>
    request<ModelsInfo>("/models/preference", { method: "PUT", body: json({ kind, ...(choice ?? {}) }), token }),

  // family (each call sends that household's private key, see lib/familyKey.ts)
  createPatient: (body: { name: string; name_bn?: string | null; age: number; district?: string | null; conditions: string[];
    consent: true; family_email?: string | null; email_opt_in?: boolean }) =>
    request<Patient & { family_key: string }>("/patients", { method: "POST", body: json(body) }),
  // a reviewer's token also opens any household (the dashboard's patient panel)
  patient: (id: number, token?: string) => request<Patient>(`/patients/${id}`, { pid: id, token }),
  items: (id: number, token?: string) => request<MedicineItem[]>(`/patients/${id}/items`, { pid: id, token }),
  addItem: (id: number, body: Partial<MedicineItem>, confirmed = false) =>
    request<MedicineItem>(`/patients/${id}/items?confirmed=${confirmed}`, { method: "POST", body: json(body), pid: id }),
  patchItem: (id: number, itemId: number, body: Partial<MedicineItem>) =>
    request<MedicineItem>(`/items/${itemId}`, { method: "PATCH", body: json(body), pid: id }),
  deleteItem: (id: number, itemId: number) => request<void>(`/items/${itemId}`, { method: "DELETE", pid: id }),

  scan: (id: number, photos: File[]) => {
    const fd = new FormData();
    photos.forEach((p) => fd.append("photos", p));
    return request<{ items: MedicineItem[]; mode: "demo" | "live"; model_id: string | null; warnings: string[] }>(
      `/patients/${id}/scan`,
      { method: "POST", body: fd, pid: id },
    );
  },
  check: (id: number) => request<{ flags_total: number; flags_new: number; review_state: string }>(
    `/patients/${id}/check`, { method: "POST", pid: id },
  ),
  status: (id: number) => request<FamilyStatus>(`/patients/${id}/status`, { pid: id }),
  familyFlags: (id: number) => request<Flag[]>(`/patients/${id}/flags?view=family`, { pid: id }),
  passport: (id: number) => request<Passport>(`/patients/${id}/passport`, { pid: id }),
  report: (id: number) => request<Report>(`/patients/${id}/report`, { pid: id }),
  nextStep: (id: number, lang: string, phrase = false) =>
    request<NextStep>(`/patients/${id}/next-step?lang=${lang}&phrase=${phrase}`, { pid: id }),
  // speech to text for Sathi's text box; 503 = use the browser's own recognition
  transcribe: (id: number, audio: Blob, lang: string) => {
    const fd = new FormData();
    fd.append("audio", audio, "speech.wav");
    fd.append("lang", lang === "bn" ? "bn" : "en");
    fd.append("patient_id", String(id));
    return request<{ text: string }>("/sathi/transcribe", { method: "POST", body: fd, pid: id });
  },
  askSathi: (id: number, question: string, lang: string) =>
    request<SathiReply>("/assistant/ask", { method: "POST", body: json({ patient_id: id, question, lang }), pid: id }),
  questions: (id: number) => request<Question[]>(`/patients/${id}/questions`, { pid: id }),
  askPharmacist: (id: number, text: string) =>
    request<Question>(`/patients/${id}/questions`, { method: "POST", body: json({ text }), pid: id }),
  questionsSeen: (id: number) => request<void>(`/patients/${id}/questions/seen`, { method: "POST", pid: id }),
  seen: (id: number, what: "results" | "passport") =>
    request<void>(`/patients/${id}/seen`, { method: "POST", body: json({ what }), pid: id }),
  patchPatient: (id: number, body: { allergies?: string[]; emergency_contact_name?: string | null;
    emergency_contact_phone?: string | null; visit_questions?: string[]; family_email?: string | null; email_opt_in?: boolean; sex?: "female" | "male" | null }) =>
    request<Patient>(`/patients/${id}`, { method: "PATCH", body: json(body), pid: id }),
  emergencyToken: (id: number) => request<{ token: string | null }>(`/patients/${id}/emergency`, { pid: id }),
  enableEmergency: (id: number) => request<{ token: string }>(`/patients/${id}/emergency`, { method: "POST", pid: id }),
  revokeEmergency: (id: number) => request<void>(`/patients/${id}/emergency`, { method: "DELETE", pid: id }),
  emergency: (token: string) => request<EmergencyPage>(`/emergency/${encodeURIComponent(token)}`),
  fhir: (id: number) => request<Record<string, unknown>>(`/patients/${id}/fhir`, { pid: id }),
  readBP: (id: number, photo: File) => {
    const fd = new FormData();
    fd.append("photo", photo);
    return request<BPPhotoReading>(`/patients/${id}/bp/read`, { method: "POST", body: fd, pid: id });
  },
  today: (id: number) => request<Today>(`/patients/${id}/today`, { pid: id }),
  savings: (id: number) => request<Savings>(`/patients/${id}/savings`, { pid: id }),
  activity: (id: number) => request<ActivityEntry[]>(`/patients/${id}/activity`, { pid: id }),
  ramadanRequest: (id: number) => request<{ ramadan_status: string | null }>(`/patients/${id}/ramadan-request`, { method: "POST", pid: id }),
  ramadanEnd: (id: number) => request<void>(`/patients/${id}/ramadan`, { method: "DELETE", pid: id }),
  demoReset: () => request<{ patient_id: number; confirmed: number; pending: number; ms: number }>("/demo/reset", { method: "POST" }),
  visit: (id: number) => request<VisitPrep>(`/patients/${id}/visit`, { pid: id }),
  visitDone: (id: number) => request<{ next: string }>(`/patients/${id}/visit/done`, { method: "POST", pid: id }),
  cleanup: (id: number) => request<{ to_set_aside: CleanupItem[]; set_aside: CleanupItem[] }>(`/patients/${id}/cleanup`, { pid: id }),
  doses: (id: number, days = 1) => request<DoseTick[]>(`/patients/${id}/doses?days=${days}`, { pid: id }),
  recordDose: (id: number, body: { item_id: number; day: string; slot: Slot; status: "taken" | "missed" }) =>
    request<DoseTick>(`/patients/${id}/doses`, { method: "POST", body: json(body), pid: id }),
  rotateFamilyKey: (id: number) => request<{ family_key: string }>(`/patients/${id}/family-key/rotate`, { method: "POST", pid: id }),
  exportHousehold: (id: number) => request<Record<string, unknown>>(`/patients/${id}/export`, { pid: id }),
  deleteHousehold: (id: number) =>
    request<void>(`/patients/${id}`, { method: "DELETE", body: json({ confirm: "DELETE" }), pid: id }),
  addBP: (id: number, body: { systolic: number; diastolic: number; pulse?: number; taken_on?: string; source?: "manual" | "photo" }) =>
    request<{ ok: true; readings: Report["bp"]["readings"] }>(`/patients/${id}/bp`, { method: "POST", body: json(body), pid: id }),

  // reviewer (token required)
  me: (token: string) => request<ReviewerAccount>("/reviewer/me", { token }),
  patients: (token: string) => request<Patient[]>("/patients", { token }),
  queue: (token: string, status = "pending_review") => request<ReviewQueue>(`/flags?status=${status}`, { token }),
  reviewerFlags: (token: string, id: number) => request<Flag[]>(`/patients/${id}/flags?view=reviewer`, { token }),
  review: (token: string, flagId: number, body: { status: "confirmed" | "dismissed"; reviewer: string; note?: string;
    checklist?: ("pack_unusual" | "unlicensed_seller")[] }) =>
    request<Flag>(`/flags/${flagId}/review`, { method: "POST", body: json(body), token }),
  undo: (token: string, flagId: number, reviewer: string) =>
    request<Flag>(`/flags/${flagId}/undo?reviewer=${encodeURIComponent(reviewer)}`, { method: "POST", token }),
  reviewerQuestions: (token: string, status: "open" | "all" = "open") =>
    request<{ questions: Question[]; open: number }>(`/questions?status=${status}`, { token }),
  reply: (token: string, qid: number, reply: string, reviewer: string) =>
    request<Question>(`/questions/${qid}/reply`, { method: "POST", body: json({ reply, reviewer }), token }),
  startNotes: (token: string, id: number) =>
    request<{ criterion: string; text: string; omitted: string; source: string }[]>(`/patients/${id}/start-notes`, { token }),
  adherence: (token: string, id: number) => request<AdherenceSummary>(`/patients/${id}/adherence`, { token }),
  kidney: (token: string, id: number) => request<KidneyView>(`/patients/${id}/kidney`, { token }),
  addKidneyTest: (token: string, id: number, body: { creatinine: number; unit: "mg/dL" | "umol/L"; taken_on: string; source: "reviewer" | "lab_report" }) =>
    request<KidneyView>(`/patients/${id}/kidney-tests`, { method: "POST", body: json(body), token }),
  bpTrend: (token: string, id: number) => request<BPTrend>(`/patients/${id}/bp-trend`, { token }),
  caseSummary: (token: string, id: number, reviewer: string) =>
    request<CaseSummary>(`/patients/${id}/case-summary?reviewer=${encodeURIComponent(reviewer)}`, { token }),
  opened: (token: string, flagId: number) => request<void>(`/flags/${flagId}/opened`, { method: "POST", token }),
  clinical: (token: string, itemId: number, body: { purpose?: string | null; purpose_bn?: string | null; stopped?: boolean; reviewer: string }) =>
    request<MedicineItem>(`/items/${itemId}/clinical`, { method: "PATCH", body: json(body), token }),
  approveSchedule: (token: string, id: number, reviewer: string) =>
    request<{ approved: number }>(`/patients/${id}/schedule/approve`, { method: "POST", body: json({ reviewer }), token }),
  confirmAllergies: (token: string, id: number, reviewer: string) =>
    request<Patient>(`/patients/${id}/allergies/confirm`, { method: "POST", body: json({ reviewer }), token }),
  ramadanRequests: (token: string) => request<RamadanRequest[]>("/ramadan/requests", { token }),
  ramadanApprove: (token: string, id: number, body: { reviewer: string; note: string; items: { item_id: number; slots: ("sehri" | "iftar")[] }[] }) =>
    request<Today>(`/patients/${id}/ramadan-approve`, { method: "POST", body: json(body), token }),
  reviewTime: () => request<{ reviews: number; median_seconds: number | null }>("/eval/review-time"),
  sathiEval: () => request<{ prompt_version: string; mode: string; run_at: string; cases: number;
    by_category: Record<string, { n: number; correct: number; rate: number; target: number }>; leaks: string[];
    latency_ms: { mean: number; p95: number } }[]>("/eval/sathi"),
  audit: (token: string, id: number) => request<AuditEntry[]>(`/patients/${id}/reviews`, { token }),

  // admin (ADMIN_TOKEN): personal reviewer invites and lost family links
  admin: {
    reviewers: (admin: string) => request<ReviewerAccount[]>("/admin/reviewers", { admin }),
    createReviewer: (admin: string, body: { name: string; role: "pharmacist" | "doctor"; reg_no?: string | null }) =>
      request<ReviewerInvite>("/admin/reviewers", { method: "POST", body: json(body), admin }),
    revoke: (admin: string, id: number) => request<ReviewerAccount>(`/admin/reviewers/${id}/revoke`, { method: "POST", admin }),
    reissue: (admin: string, id: number) => request<ReviewerInvite>(`/admin/reviewers/${id}/reissue`, { method: "POST", admin }),
    familyLink: (admin: string, pid: number) =>
      request<{ family_key: string; family_url: string }>(`/admin/patients/${pid}/family-key`, { method: "POST", admin }),
  },
};
