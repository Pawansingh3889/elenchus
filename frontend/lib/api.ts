import { useUserStore } from "./store";
import type {
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const userId = useUserStore.getState().currentUserId;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (userId) headers["X-User-Id"] = userId;

  const res = await fetch(`${BASE}/api/v1${path}`, { ...init, headers });
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body?.error?.message ?? body?.detail ?? message;
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
    request<Template>("/templates/generate", { method: "POST", body: JSON.stringify({ prompt }) }),
  listPublished: () => request<TemplateSummary[]>("/templates/published"),
  startRun: (templateId: string) =>
    request<Run>("/runs", { method: "POST", body: JSON.stringify({ template_id: templateId }) }),
  getRun: (id: string) => request<Run>(`/runs/${id}`),
  sendRunMessage: (id: string, content: string) =>
    request<Run>(`/runs/${id}/messages`, { method: "POST", body: JSON.stringify({ content }) }),
  listTemplateRuns: (templateId: string) => request<RunSummary[]>(`/templates/${templateId}/runs`),
  getTemplateRun: (templateId: string, runId: string) =>
    request<RunDetail>(`/templates/${templateId}/runs/${runId}`),
};
