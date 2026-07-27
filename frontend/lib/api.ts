import { useUserStore } from "./store";
import type {
  GeneratedTemplate,
  Run,
  RunDetail,
  RunSummary,
  Template,
  TemplateSummary,
  TemplateVersion,
  TemplateWrite,
  User,
} from "./types";

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
 *  "[object Object]", which is what an author saw for a blank title or a duplicate
 *  option — so flatten it into the field and the reason. */
function errorMessage(body: unknown, fallback: string): string {
  const payload = body as { error?: { message?: unknown }; detail?: unknown } | null;
  const detail = payload?.error?.message ?? payload?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const reasons = detail
      .map((item) => {
        const { loc, msg } = (item ?? {}) as { loc?: unknown; msg?: unknown };
        // Pydantic prefixes custom validators with "Value error, "; it means nothing here.
        const reason = String(msg ?? "").replace(/^Value error, /, "");
        const field = Array.isArray(loc)
          ? loc.filter((part) => part !== "body").join(".")
          : "";
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

  const res = await fetch(`${BASE}/api/v1${path}`, { ...init, headers });
  if (!res.ok) {
    let message = res.statusText;
    try {
      message = errorMessage(await res.json(), message);
    } catch {
      // non-JSON error body; keep the status text
    }
    throw new ApiError(message, res.status);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** For file downloads: same auth header, but the raw Response instead of parsed JSON. */
async function rawRequest(path: string): Promise<Response> {
  const userId = useUserStore.getState().currentUserId;
  const headers: Record<string, string> = {};
  if (userId) headers["X-User-Id"] = userId;
  const res = await fetch(`${BASE}/api/v1${path}`, { headers });
  if (!res.ok) throw new ApiError(res.statusText, res.status);
  return res;
}

export const api = {
  listUsers: () => request<User[]>("/users"),
  listTemplates: () => request<TemplateSummary[]>("/templates"),
  getTemplate: (id: string) => request<Template>(`/templates/${id}`),
  createTemplate: (data: TemplateWrite) =>
    request<Template>("/templates", { method: "POST", body: JSON.stringify(data) }),
  updateTemplate: (id: string, data: TemplateWrite) =>
    request<Template>(`/templates/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteTemplate: (id: string) => request<void>(`/templates/${id}`, { method: "DELETE" }),
  publishTemplate: (id: string) =>
    request<TemplateVersion>(`/templates/${id}/publish`, { method: "POST" }),
  generateTemplate: (prompt: string) =>
    request<GeneratedTemplate>("/templates/generate", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),
  refineTemplate: (id: string, instruction: string) =>
    request<GeneratedTemplate>(`/templates/${id}/refine`, {
      method: "POST",
      body: JSON.stringify({ instruction }),
    }),
  listPublished: () => request<TemplateSummary[]>("/templates/published"),
  startRun: (templateId: string) =>
    request<Run>("/runs", { method: "POST", body: JSON.stringify({ template_id: templateId }) }),
  getRun: (id: string) => request<Run>(`/runs/${id}`),
  sendRunMessage: (id: string, content: string) =>
    request<Run>(`/runs/${id}/messages`, { method: "POST", body: JSON.stringify({ content }) }),
  listTemplateRuns: (templateId: string) => request<RunSummary[]>(`/templates/${templateId}/runs`),
  exportRuns: (templateId: string, format: "csv" | "json") =>
    rawRequest(`/templates/${templateId}/runs/export?format=${format}`),
  getTemplateRun: (templateId: string, runId: string) =>
    request<RunDetail>(`/templates/${templateId}/runs/${runId}`),
};
