export type ApiList<T> = T[] | { results: T[]; count?: number; next?: string | null; previous?: string | null };
export type Estate = { id: string; name: string; estate_code: string; status: string; address: string; timezone: string };
export type Resident = { id: string; user?: { email?: string; first_name?: string; last_name?: string }; estate?: string; status: string; submitted_at?: string };
export type Invitation = { id: string; visitor_name: string; visitor_phone?: string; unit_number?: string; valid_from: string; valid_until: string; status: string; access_type: string };
export type GateEvent = { id: string; invitation: string; visitor_name: string; event_type: string; status: string; occurred_at: string; reason?: string; gate_device: string };
export type AuditEntry = { id: string; created_at: string; actor_email?: string; action: string; resource_type: string; resource_id: string; estate_id?: string | null };

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch("/api/bff/" + path.replace(/^\//, ""), {
    ...init,
    headers,
    credentials: "same-origin",
    cache: "no-store",
  });
  if (response.status === 401 && typeof window !== "undefined") window.location.assign("/login");
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || data.non_field_errors?.[0] || data.error?.message || "Request failed (" + response.status + ")");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export function listOf<T>(value: ApiList<T>): T[] { return Array.isArray(value) ? value : value.results; }
