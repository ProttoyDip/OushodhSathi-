import type {
  AuditEntry, EvalResult, FamilyStatus, Flag, Health, MedicineItem, ModelsInfo, Passport, Patient, PilotStats, Report, ReviewQueue,
} from "./types";
import { familyKey } from "./familyKey";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit & { token?: string; pid?: number } = {}): Promise<T> {
  const { token, pid, headers, ...rest } = init;
  const key = pid !== undefined ? familyKey(pid) : null;
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...rest,
      headers: {
        ...(rest.body && !(rest.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
        ...(token ? { "X-Reviewer-Token": token } : {}),
        ...(key ? { "X-Family-Key": key } : {}),
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
  createPatient: (body: { name: string; name_bn?: string | null; age: number; district?: string | null; conditions: string[] }) =>
    request<Patient & { family_key: string }>("/patients", { method: "POST", body: json(body) }),
  patient: (id: number) => request<Patient>(`/patients/${id}`, { pid: id }),
  items: (id: number) => request<MedicineItem[]>(`/patients/${id}/items`, { pid: id }),
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
  addBP: (id: number, body: { systolic: number; diastolic: number; taken_on?: string }) =>
    request<{ ok: true; readings: Report["bp"]["readings"] }>(`/patients/${id}/bp`, { method: "POST", body: json(body), pid: id }),

  // reviewer (token required)
  patients: (token: string) => request<(Patient & { family_key: string })[]>("/patients", { token }),
  queue: (token: string, status = "pending_review") => request<ReviewQueue>(`/flags?status=${status}`, { token }),
  reviewerFlags: (token: string, id: number) => request<Flag[]>(`/patients/${id}/flags?view=reviewer`, { token }),
  review: (token: string, flagId: number, body: { status: "confirmed" | "dismissed"; reviewer: string; note?: string }) =>
    request<Flag>(`/flags/${flagId}/review`, { method: "POST", body: json(body), token }),
  undo: (token: string, flagId: number, reviewer: string) =>
    request<Flag>(`/flags/${flagId}/undo?reviewer=${encodeURIComponent(reviewer)}`, { method: "POST", token }),
  audit: (token: string, id: number) => request<AuditEntry[]>(`/patients/${id}/reviews`, { token }),
};
