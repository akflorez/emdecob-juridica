const BASE_URL = import.meta.env.VITE_API_BASE_URL as string;

export type ApiErrorPayload = { detail?: any } | any;

export class ApiError extends Error {
  status: number;
  payload?: ApiErrorPayload;
  constructor(status: number, message: string, payload?: ApiErrorPayload) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

function getToken() {
  return localStorage.getItem("access_token");
}

async function parseError(res: Response) {
  const text = await res.text().catch(() => "");
  try {
    return text ? JSON.parse(text) : undefined;
  } catch {
    return text;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  auth = true
): Promise<T> {
  if (!BASE_URL) throw new Error("VITE_API_BASE_URL no está definido");

  const headers = new Headers(options.headers || {});
  const isFormData = options.body instanceof FormData;
  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const payload = await parseError(res);
    const msg =
      (payload && (payload.detail || payload.message)) ||
      `Error ${res.status}`;
    throw new ApiError(res.status, String(msg), payload);
  }

  if (res.status === 204) return undefined as T;

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return (await res.json()) as T;

  return (await res.text()) as unknown as T;
}

// -------------------
// AUTH
// -------------------
export type LoginResponse = { access_token: string; role: "ADMIN" | "ABOGADO" };

export function login(username: string, password: string) {
  return apiFetch<LoginResponse>(
    "/auth/login",
    { method: "POST", body: JSON.stringify({ username, password }) },
    false
  );
}

// -------------------
// CASES
// -------------------
export type CaseOut = {
  id: number;
  radicado: string;
  demandante?: string | null;
  demandado?: string | null;
  juzgado?: string | null;
  alias?: string | null;

  // 🔥 nuevos (para tu UI)
  id_proceso_rama?: number | null;
  unread_count?: number;      // tipo correo no leído
  new_events?: number;        // cuántos llegaron en el último sync
  last_sync_at?: string | null;

  // opcional si lo devuelves
  created_at?: string;
  updated_at?: string;

  // si quieres tabs en detalle
  raw_proceso?: any;
  raw_detalle?: any;
};

export type CasesListResponse = { items: CaseOut[] };

// 1) CONSULTA “SIMPLE” (si la dejas)
export function getCaseByRadicado(radicado: string) {
  const r = encodeURIComponent(radicado.trim());
  return apiFetch<CaseOut>(`/cases/by-radicado/${r}`);
}

// 2) ✅ CONSULTA + GUARDA + ACTUALIZA + MARCA NOVEDADES
export function syncCaseByRadicado(radicado: string) {
  const r = encodeURIComponent(radicado.trim());
  return apiFetch<CaseOut>(`/cases/by-radicado/${r}/sync`, { method: "POST" });
}

// 3) ✅ “Todos los casos”
export function getCases() {
  return apiFetch<CasesListResponse>(`/cases`);
}

// 4) ✅ marcar caso como leído (quitar badge)
export function markCaseRead(caseId: number) {
  return apiFetch<{ ok: true; id: number; unread_count: number }>(
    `/cases/${caseId}/mark-read`,
    { method: "POST" }
  );
}

// -------------------
// EVENTS
// -------------------
export type EventOut = {
  event_date?: string | null;
  title?: string | null;
  detail?: string | null;
  created_at?: string | null;
  raw?: any;
};

export function getCaseEvents(caseId: number) {
  return apiFetch<{ items: EventOut[]; case?: { id: number; radicado: string; unread_count: number } }>(
    `/cases/${caseId}/events`
  );
}

// -------------------
// IMPORT EXCEL
// -------------------
export function importExcel(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return apiFetch<any>("/cases/import-excel", { method: "POST", body: fd });
}
