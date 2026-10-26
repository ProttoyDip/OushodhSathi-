import type {
  AuditEntry, EvalResult, FamilyStatus, Flag, Health, MedicineItem, Passport, Patient, Report, ReviewQueue,
} from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit & { token?: string } = {}): Promise<T> {
  const { token, headers, ...rest } = init;
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...rest,
      headers: {
        ...(rest.body && !(rest.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
        ...(token ? { "X-Reviewer-Token": token } : {}),
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

  patients: () => request<Patient[]>("/patients"),
  patient: (id: number) => request<Patient>(`/patients/${id}`),
  items: (id: number) => request<MedicineItem[]>(`/patients/${id}/items`),
  addItem: (id: number, body: Partial<MedicineItem>, confirmed = false) =>
    request<MedicineItem>(`/patients/${id}/items?confirmed=${confirmed}`, { method: "POST", body: json(body) }),
  patchItem: (itemId: number, body: Partial<MedicineItem>) =>
    request<MedicineItem>(`/items/${itemId}`, { method: "PATCH", body: json(body) }),
  deleteItem: (itemId: number) => request<void>(`/items/${itemId}`, { method: "DELETE" }),

  scan: (id: number, photos: File[]) => {
    const fd = new FormData();
    photos.forEach((p) => fd.append("photos", p));
    return request<{ items: MedicineItem[]; mode: "demo" | "live"; model_id: string | null; warnings: string[] }>(
      `/patients/${id}/scan`,
      { method: "POST", body: fd },
    );
  },
  check: (id: number) => request<{ flags_total: number; flags_new: number; review_state: string }>(
    `/patients/${id}/check`, { method: "POST" },
  ),
  status: (id: number) => request<FamilyStatus>(`/patients/${id}/status`),
  familyFlags: (id: number) => request<Flag[]>(`/patients/${id}/flags?view=family`),
  passport: (id: number) => request<Passport>(`/patients/${id}/passport`),
  report: (id: number) => request<Report>(`/patients/${id}/report`),

  // reviewer (token required)
  queue: (token: string, status = "pending_review") => request<ReviewQueue>(`/flags?status=${status}`, { token }),
  reviewerFlags: (token: string, id: number) => request<Flag[]>(`/patients/${id}/flags?view=reviewer`, { token }),
  review: (token: string, flagId: number, body: { status: "confirmed" | "dismissed"; reviewer: string; note?: string }) =>
    request<Flag>(`/flags/${flagId}/review`, { method: "POST", body: json(body), token }),
  undo: (token: string, flagId: number, reviewer: string) =>
    request<Flag>(`/flags/${flagId}/undo?reviewer=${encodeURIComponent(reviewer)}`, { method: "POST", token }),
  audit: (token: string, id: number) => request<AuditEntry[]>(`/patients/${id}/reviews`, { token }),
};
