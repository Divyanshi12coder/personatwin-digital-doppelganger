// Thin, typed HTTP client for the PersonaTwin API.
// The browser only ever talks to our backend — never to an LLM provider —
// so no AI keys exist anywhere in the frontend bundle.

const RAW_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "";
export const API_BASE = RAW_BASE.replace(/\/+$/, "");
const TOKEN_KEY = "personatwin.token";

export class ApiError extends Error {
  status: number;
  fieldErrors: { field: string; message: string }[];

  constructor(status: number, message: string, fieldErrors: { field: string; message: string }[] = []) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

let unauthorizedHandler: (() => void) | null = null;

export const tokenStore = {
  get: (): string | null => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set: (token: string) => {
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch {
      /* storage unavailable (private mode) — the session lasts for this tab only */
    }
  },
  clear: () => {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* ignore */
    }
  },
};

export function onUnauthorized(handler: () => void) {
  unauthorizedHandler = handler;
}

type Body = Record<string, unknown> | unknown[] | FormData | undefined;

async function request<T>(method: string, path: string, body?: Body, signal?: AbortSignal): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  const token = tokenStore.get();
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api${path}`, { method, headers, body: payload, signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(0, "Can't reach the PersonaTwin server. Check your connection and try again.");
  }

  if (res.status === 204) return undefined as T;
  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    const obj = (data ?? {}) as { detail?: unknown; errors?: { field: string; message: string }[] };
    const detail =
      typeof obj.detail === "string"
        ? obj.detail
        : res.status >= 500
          ? "Something went wrong on our side. Please try again."
          : `Request failed (${res.status})`;
    if (res.status === 401 && token) unauthorizedHandler?.();
    throw new ApiError(res.status, detail, obj.errors ?? []);
  }
  return data as T;
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>("GET", path, undefined, signal),
  post: <T>(path: string, body?: Body) => request<T>("POST", path, body),
  put: <T>(path: string, body?: Body) => request<T>("PUT", path, body),
  patch: <T>(path: string, body?: Body) => request<T>("PATCH", path, body),
  del: <T>(path: string, body?: Body) => request<T>("DELETE", path, body),
};

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "Something unexpected happened.";
}
