import type {
  CachedSearch,
  LeadStatus,
  Prospect,
  ProspectFilters,
  SearchRequest,
  SearchResponse,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new ApiError(res.status, text || `${res.status} ${res.statusText}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function qs(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  listProspects: (filters: ProspectFilters = {}) =>
    request<Prospect[]>(`/api/prospects${qs(filters)}`),

  getProspect: (placeId: string) =>
    request<Prospect>(`/api/prospects/${encodeURIComponent(placeId)}`),

  updateProspect: (
    placeId: string,
    payload: { status?: LeadStatus; notes?: string | null },
  ) =>
    request<Prospect>(`/api/prospects/${encodeURIComponent(placeId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteProspect: (placeId: string) =>
    request<void>(`/api/prospects/${encodeURIComponent(placeId)}`, {
      method: "DELETE",
    }),

  listSearches: () => request<CachedSearch[]>("/api/searches"),

  createSearch: (req: SearchRequest) =>
    request<SearchResponse>("/api/searches", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  deleteSearch: (searchId: number) =>
    request<void>(`/api/searches/${searchId}`, { method: "DELETE" }),
};

export { ApiError };
