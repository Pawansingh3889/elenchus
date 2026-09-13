import { useLocaleStore, useUserStore } from "./store";
import type { ResumableRun, Run, TemplateSummary, User } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Carries the status so callers can tell "you may not" from "it broke". */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Our own errors carry `detail` as a string, but FastAPI's request validation returns a
 *  list of `{loc, msg}` instead. Passing that list to Error() stringifies it to
 *  "[object Object]", so flatten it into something readable. */
function errorDetail(body: unknown, fallback: string): string {
  const payload = body as { error?: { message?: unknown }; detail?: unknown } | null;
  const detail = payload?.error?.message ?? payload?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const reasons = detail
      .map((item) => {
        const { loc, msg } = (item ?? {}) as { loc?: unknown; msg?: unknown };
        // Pydantic prefixes custom validators with "Value error, "; it means nothing here.
        const reason = String(msg ?? "").replace(/^Value error, /, "");
        const field = Array.isArray(loc) ? loc.filter((part) => part !== "body").join(".") : "";
        return field ? `${field}: ${reason}` : reason;
      })
      .filter(Boolean);
    if (reasons.length) return reasons.join("; ");
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const userId = useUserStore.getState().currentUserId;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (userId) headers["X-User-Id"] = userId;
  // Read out of band like the user id, so every call carries the language without each
  // caller remembering to pass it. The backend answers its own messages in this
  // language, and a run started now is conducted in it.
  headers["Accept-Language"] = useLocaleStore.getState().locale;

  const res = await fetch(`${BASE}/api/v1${path}`, {
    ...init,
    headers,
    // The session set by a Microsoft or Google sign-in is an HttpOnly cookie on the API's
    // origin, and the browser will not attach it cross-origin without this. The dev
    // header above still works when no cookie exists, which is what local runs use.
    credentials: "include",
  });
  if (!res.ok) {
    let message = res.statusText;
    try {
      message = errorDetail(await res.json(), res.statusText);
    } catch {
      // non-JSON error body; keep the status text
    }
    throw new ApiError(message, res.status);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  listUsers: () => request<User[]>("/users"),
  /** Which real sign-in providers this deployment offers. Unauthenticated: the browser
   *  has to ask before anyone is signed in. */
  providers: () => request<{ providers: string[] }>("/auth/providers"),
  /** Who the session cookie says this is, or null when there is no live session.
   *
   *  A 401 here is an answer, not a failure: the browser cannot read an HttpOnly cookie,
   *  so asking the server is the only way to tell a signed-in visitor from a signed-out
   *  one, and "nobody" has to come back as a value rather than as a thrown error.
   *
   *  Sends X-User-Id like every other call. Without it, a cookie-less browser always
   *  resolved through the server's own "nobody sent an id" default, so the picker in the
   *  top bar could set the store and watch it get overwritten on the next render. The
   *  cookie still wins when one is present. */
  session: async (): Promise<User | null> => {
    const userId = useUserStore.getState().currentUserId;
    const headers: Record<string, string> = {};
    if (userId) headers["X-User-Id"] = userId;
    const res = await fetch(`${BASE}/api/v1/auth/me`, { headers, credentials: "include" });
    return res.ok ? ((await res.json()) as User) : null;
  },
  /** Trade an address for the id the header shim uses as a session. The only way into
   *  the app from a browser with empty storage: listing users needs a caller, and a
   *  caller is an id, and that list was the only place to get one. Dev-only on the
   *  server, which is where it is guarded. */
  identify: (email: string) =>
    request<User>("/dev/identify", { method: "POST", body: JSON.stringify({ email }) }),
  /** Wipe all data and re-seed. Demo mode only. */
  resetDemo: () =>
    request<{ status: string; users: number; surveys: number }>("/dev/reset", { method: "POST" }),
  listPublished: () => request<TemplateSummary[]>("/templates/published"),
  startRun: (templateId: string) =>
    request<Run>("/runs", { method: "POST", body: JSON.stringify({ template_id: templateId }) }),
  getRun: (id: string) => request<Run>(`/runs/${id}`),
  myUnfinishedRuns: () => request<ResumableRun[]>("/runs"),
  sendRunMessage: (id: string, content: string) =>
    request<Run>(`/runs/${id}/messages`, { method: "POST", body: JSON.stringify({ content }) }),
  // No body: which answer comes back is the engine's to decide, not the client's.
  rewindRun: (id: string) => request<Run>(`/runs/${id}/rewind`, { method: "POST" }),
  /** Erase a run and everything in it. 204, so there is nothing to unwrap. */
  deleteRun: (id: string) => request<void>(`/runs/${id}`, { method: "DELETE" }),
};
