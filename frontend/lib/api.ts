// Typed fetch wrapper for the MediShield FastAPI backend.

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

// --- Shared response types (mirror backend Pydantic schemas) ----------------

export type CaseStatus =
  | "RECEIVED"
  | "CLASSIFIED"
  | "PROCESSING"
  | "DECIDED"
  | "FAILED";

export type Decision = "APPROVE" | "REJECT" | "ESCALATE";

export interface CaseListItem {
  case_id: string;
  status: CaseStatus;
  document_type: string | null;
  decision: Decision | null;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface CaseListResponse {
  items: CaseListItem[];
  total: number;
}

export interface CaseDetail {
  case_id: string;
  uploaded_by: number;
  status: CaseStatus;
  document_type: string | null;
  document_path: string;
  decision: Decision | null;
  confidence: number | null;
  justification: string | null;
  agent_outputs: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface UploadResponse {
  case_id: string;
  status: CaseStatus;
}

// --- Internal fetch helper --------------------------------------------------

interface FetchOpts extends Omit<RequestInit, "body"> {
  token?: string;
  json?: unknown;
  form?: FormData;
}

async function apiFetch<T>(path: string, opts: FetchOpts = {}): Promise<T> {
  const headers = new Headers(opts.headers);
  if (opts.token) headers.set("Authorization", `Bearer ${opts.token}`);

  let body: BodyInit | undefined;
  if (opts.form) {
    body = opts.form; // Let the browser set the multipart boundary.
  } else if (opts.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(opts.json);
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...opts, headers, body });
  if (!res.ok) {
    let detail = await res.text();
    try {
      detail = (JSON.parse(detail) as { detail?: string }).detail ?? detail;
    } catch {
      // not JSON, keep raw text
    }
    throw new Error(`API ${res.status}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// --- Public methods ---------------------------------------------------------

export function listCases(token: string, statusFilter?: CaseStatus) {
  const qs = statusFilter ? `?status=${statusFilter}` : "";
  return apiFetch<CaseListResponse>(`/cases${qs}`, { token });
}

export function getCase(token: string, caseId: string) {
  return apiFetch<CaseDetail>(`/cases/${caseId}`, { token });
}

export function uploadCase(token: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<UploadResponse>("/cases/upload", {
    method: "POST",
    token,
    form,
  });
}

export function overrideCase(
  token: string,
  caseId: string,
  decision: Decision,
  note: string,
) {
  return apiFetch<CaseDetail>(`/cases/${caseId}/override`, {
    method: "POST",
    token,
    json: { decision, note },
  });
}

export function fetchMe(token: string) {
  return apiFetch<{ id: number; email: string; name: string; role: string }>(
    "/auth/me",
    { token },
  );
}
