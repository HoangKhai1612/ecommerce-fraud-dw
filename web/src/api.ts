export type {
  PredictionRecord,
  PredictionListItem,
  PredictionsListResponse,
  TransactionSample,
  ServiceStatus,
  SystemStatusResponse,
  ExplainResponse,
} from "./types";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? "/api" : "/api");

export async function apiRequest(
  path: string,
  opts?: RequestInit
): Promise<Response> {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const url = path.startsWith("http") ? path : `${API_BASE_URL}${cleanPath}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...opts?.headers },
    ...opts,
  });
  return res;
}

export async function apiJson<T = unknown>(
  path: string,
  opts?: RequestInit
): Promise<T> {
  const res = await apiRequest(path, opts);
  let body: any = null;
  const text = await res.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }
  if (!res.ok) {
    const err: any = new Error(
      (body && (body.detail || body.message)) || `HTTP ${res.status}`
    );
    (err as any).status = res.status;
    (err as any).body = body;
    throw err;
  }
  return body as T;
}
