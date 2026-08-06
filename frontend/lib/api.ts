import { useLocaleStore, useUserStore } from "./store";
import type {
  GeneratedTemplate,
  Run,
  ResumableRun,
  RunDetail,
  RunSummary,
  RunSummaryContent,
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
  /** 0-based indexes of the questions the server complained about, so the builder can
   *  mark those cards instead of leaving the author to match a message to a question. */
  readonly questions: number[];

  constructor(message: string, status: number, questions: number[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.questions = questions;
  }
}

/** The field names an author would recognise, for the ones worth naming at all. */
const FIELD_LABELS: Record<string, string> = {
  text: "question text",
  options: "options",
  answer_type: "answer type",
  show_when: "visibility condition",
  title: "title",
  description: "description",
};

/**
 * Turn one `{loc, msg}` entry into something an author can act on.
 *
 * `loc` is a path into the request body, 0-indexed: `["body", "questions", 1,
 * "show_when", "value"]`. Joining it with dots produced "questions.1.show_when.value",
 * which is both jargon and, worse, off by one against a builder that numbers its cards
 * from 1, so an author reading it inspected the wrong question. The backend's own
 * hand-written validators already say "question 2's condition wants…"; this brings the
 * field-level errors into the same voice.
 */
function describe(loc: unknown[], msg: string): { text: string; question?: number } {
  const path = loc.filter((part) => part !== "body");
  const [head, index, ...rest] = path;

  if (head === "questions" && typeof index === "number") {
    // Object.hasOwn, not `in`: `in` walks the prototype, so a path part called
    // "constructor" would resolve to a function and render as one.
    const field = rest.find((part) => typeof part === "string" && Object.hasOwn(FIELD_LABELS, part));
    const named = typeof field === "string" ? ` (${FIELD_LABELS[field]})` : "";
    return { text: `Question ${index + 1}${named}: ${msg}`, question: index };
  }
  if (typeof head === "string" && Object.hasOwn(FIELD_LABELS, head)) {
    return { text: `The ${FIELD_LABELS[head]}: ${msg}` };
  }
  const field = path.join(".");
  return { text: field ? `${field}: ${msg}` : msg };
}

/** Our own errors carry `detail` as a string, but FastAPI's request validation returns a
 *  list of `{loc, msg}` instead. Passing that list to Error() stringifies it to
 *  "[object Object]", which is what an author saw for a blank title or a duplicate
 *  option, so flatten it into something readable and record which question each
 *  complaint belongs to so the builder can mark that card. */
function errorDetail(body: unknown, fallback: string): { message: string; questions: number[] } {
  const payload = body as { error?: { message?: unknown }; detail?: unknown } | null;
  const detail = payload?.error?.message ?? payload?.detail;
  if (typeof detail === "string") return { message: detail, questions: [] };
  if (Array.isArray(detail)) {
    const questions: number[] = [];
    const reasons = detail
      .map((item) => {
        const { loc, msg } = (item ?? {}) as { loc?: unknown; msg?: unknown };
        // Pydantic prefixes custom validators with "Value error, "; it means nothing here.
        const reason = String(msg ?? "").replace(/^Value error, /, "");
        const described = describe(Array.isArray(loc) ? loc : [], reason);
        if (described.question !== undefined && !questions.includes(described.question)) {
          questions.push(described.question);
        }
        return described.text;
      })
      .filter(Boolean);
    if (reasons.length) return { message: reasons.join("; "), questions };
  }
  return { message: fallback, questions: [] };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const userId = useUserStore.getState().currentUserId;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (userId) headers["X-User-Id"] = userId;
  // Read out of band like the user id, so every call carries the language without each
  // caller remembering to pass it. The backend answers its own messages in this
  // language, and a run started now is conducted in it.
  headers["Accept-Language"] = useLocaleStore.getState().locale;

  const res = await fetch(`${BASE}/api/v1${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = { message: res.statusText, questions: [] as number[] };
    try {
      detail = errorDetail(await res.json(), res.statusText);
    } catch {
      // non-JSON error body; keep the status text
    }
    throw new ApiError(detail.message, res.status, detail.questions);
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
  myUnfinishedRuns: () => request<ResumableRun[]>("/runs"),
  sendRunMessage: (id: string, content: string) =>
    request<Run>(`/runs/${id}/messages`, { method: "POST", body: JSON.stringify({ content }) }),
  listTemplateRuns: (templateId: string) => request<RunSummary[]>(`/templates/${templateId}/runs`),
  exportRuns: (templateId: string, format: "csv" | "json") =>
    rawRequest(`/templates/${templateId}/runs/export?format=${format}`),
  getTemplateRun: (templateId: string, runId: string) =>
    request<RunDetail>(`/templates/${templateId}/runs/${runId}`),
  summariseRun: (templateId: string, runId: string, refresh = false) =>
    request<RunSummaryContent>(
      `/templates/${templateId}/runs/${runId}/summary${refresh ? "?refresh=true" : ""}`,
      { method: "POST" },
    ),
};
