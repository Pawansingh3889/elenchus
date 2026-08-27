import { z, type ZodType } from "zod";

import { dashboardSchema, surveyReportSchema } from "./schemas";
import { useLocaleStore, useUserStore } from "./store";
import type {
  Account,
  AccountChangeEntry,
  AccountCreate,
  AccountImpact,
  AccountWrite,
  AdminHealthRead,
  AnswersMatrix,
  AudienceReach,
  EvalAccuracyReport,
  GeneratedTemplate,
  LlmEntry,
  LlmLedger,
  LlmReport,
  Me,
  Person,
  RespondentRow,
  ResumableRun,
  Run,
  RunDetail,
  RunSummary,
  RunSummaryContent,
  SurveyAudience,
  SurveyRecapStatus,
  SurveySummary,
  Template,
  TemplateSummary,
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
  audience: "audience",
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

/**
 * Thrown when the server answered successfully but not in the shape this app renders.
 *
 * Separate from ApiError on purpose: an ApiError means the request was refused and the
 * message belongs to the person, while this means the contract broke and the message
 * belongs to whoever is going to fix it. Carries the failing field paths, because
 * "expected number, received string at questions.3.average" is a bug report and
 * "invalid response" is not.
 */
export class ApiContractError extends Error {
  readonly status = 200;
  readonly issues: string[];

  constructor(path: string, issues: string[]) {
    super(`${path} answered in an unexpected shape: ${issues.join("; ")}`);
    this.name = "ApiContractError";
    this.issues = issues;
  }
}

/** Validate a parsed body against the schema for this endpoint, or throw loudly. */
function parseBody<S extends ZodType>(path: string, schema: S, body: unknown): z.infer<S> {
  const result = schema.safeParse(body);
  if (result.success) return result.data;
  // Cap the list: a wholesale shape change produces an issue per field, and thirty of
  // them in one message helps nobody read the first three.
  const issues = result.error.issues
    .slice(0, 5)
    .map((i) => `${i.path.join(".") || "(root)"}: ${i.message}`);
  throw new ApiContractError(path, issues);
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

/**
 * `request`, with the response validated before it is handed back.
 *
 * The plain `request` above still casts, which is what every endpoint not yet given a
 * schema uses. Prefer this one: a cast is a claim nobody checks, and the fields this
 * app turns into figures on a page are exactly the ones worth checking.
 */
async function requestParsed<S extends ZodType>(
  path: string,
  schema: S,
  init?: RequestInit,
): Promise<z.infer<S>> {
  return parseBody(path, schema, await request<unknown>(path, init));
}

export const api = {
  listUsers: () => request<User[]>("/users"),
  dashboard: () => requestParsed("/dashboard", dashboardSchema),
  report: (id: string) => requestParsed(`/templates/${id}/report`, surveyReportSchema),
  getTemplate: (id: string) => request<Template>(`/templates/${id}`),
  createTemplate: (data: TemplateWrite) =>
    request<Template>("/templates", { method: "POST", body: JSON.stringify(data) }),
  updateTemplate: (id: string, data: TemplateWrite) =>
    request<Template>(`/templates/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteTemplate: (id: string) => request<void>(`/templates/${id}`, { method: "DELETE" }),
  publishTemplate: (id: string) =>
    request<Template>(`/templates/${id}/publish`, { method: "POST" }),
  closeTemplate: (id: string) =>
    request<Template>(`/templates/${id}/close`, { method: "POST" }),
  generateTemplate: (
    prompt: string,
    audience: SurveyAudience,
    audienceUserId: string | null = null,
  ) =>
    request<GeneratedTemplate>("/templates/generate", {
      method: "POST",
      body: JSON.stringify({ prompt, audience, audience_user_id: audienceUserId }),
    }),
  refineTemplate: (id: string, instruction: string) =>
    request<GeneratedTemplate>(`/templates/${id}/refine`, {
      method: "POST",
      body: JSON.stringify({ instruction }),
    }),
  listPeople: () => request<Person[]>("/people"),
  me: () => request<Me>("/me"),
  /** Trade an address for the id the header shim uses as a session. The only way into
   *  the app from a browser with empty storage: listing users needs a caller, and a
   *  caller is an id, and that list was the only place to get one. Dev-only on the
   *  server, which is where it is guarded. */
  /** Which real sign-in providers this deployment offers. Unauthenticated: the browser
   *  has to ask before anyone is signed in. */
  providers: () => request<{ providers: string[] }>("/auth/providers"),
  /** Who the session cookie says this is, or null when there is no live session.
   *
   *  A 401 here is an answer, not a failure: the browser cannot read an HttpOnly cookie,
   *  so asking the server is the only way to tell a signed-in visitor from a signed-out
   *  one, and "nobody" has to come back as a value rather than as a thrown error.
   *
   *  Sends X-User-Id like every other call, which `request` does and this one used not
   *  to: without it, a cookie-less browser always resolved through the server's own
   *  "nobody sent an id" default, which meant the picker in the top bar could set the
   *  store and watch it get overwritten back to that default on the next render. The
   *  cookie still wins when one is present, exactly as before; this only changes what
   *  the server sees when there isn't one. */
  session: async (): Promise<User | null> => {
    const userId = useUserStore.getState().currentUserId;
    const headers: Record<string, string> = {};
    if (userId) headers["X-User-Id"] = userId;
    const res = await fetch(`${BASE}/api/v1/auth/me`, { headers, credentials: "include" });
    return res.ok ? ((await res.json()) as User) : null;
  },
  identify: (email: string) =>
    request<User>("/dev/identify", { method: "POST", body: JSON.stringify({ email }) }),
  /** Wipe all data and re-seed. Demo mode only. */
  resetDemo: () => request<{ status: string; users: number; surveys: number }>("/dev/reset", { method: "POST" }),
  createAccount: (data: AccountCreate) =>
    request<Account>("/admin/users", { method: "POST", body: JSON.stringify(data) }),
  /** A full replacement, which is what makes removing a group expressible: a body that
   *  only ever added could not move somebody off a line. */
  replaceAccount: (id: string, data: AccountWrite) =>
    request<Account>(`/admin/users/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  /** What saving this edit would change, without saving it. POST for the body only:
   *  the server writes nothing. */
  previewAccount: (id: string, data: AccountWrite) =>
    request<AccountImpact>(`/admin/users/${id}/preview`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  accountHistory: (id: string) => request<AccountChangeEntry[]>(`/admin/users/${id}/history`),
  /** Live headcount per audience, for the screens that aim a survey. */
  audienceReach: () => request<AudienceReach>("/people/reach"),
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
  listTemplateRuns: (templateId: string) => request<RunSummary[]>(`/templates/${templateId}/runs`),
  getTemplateRun: (templateId: string, runId: string) =>
    request<RunDetail>(`/templates/${templateId}/runs/${runId}`),
  /** The recap already stored, if the results have not moved past it. A GET, so
   *  reading one costs no model call; POST is what writes a new one. */
  surveyRecap: (templateId: string) =>
    request<SurveyRecapStatus>(`/templates/${templateId}/summary`),
  answersMatrix: (templateId: string) =>
    request<AnswersMatrix>(`/templates/${templateId}/answers`),
  summariseSurvey: (templateId: string, refresh = false) =>
    request<SurveySummary>(
      `/templates/${templateId}/summary${refresh ? "?refresh=true" : ""}`,
      { method: "POST" },
    ),
  summariseRun: (templateId: string, runId: string, refresh = false) =>
    request<RunSummaryContent>(
      `/templates/${templateId}/runs/${runId}/summary${refresh ? "?refresh=true" : ""}`,
      { method: "POST" },
    ),
  listRespondents: (templateId: string) =>
    request<RespondentRow[]>(`/templates/${templateId}/respondents`),
  streamRespondents: (templateId: string) =>
    fetch(`${BASE}/api/v1/templates/${templateId}/respondents/stream`, {
      credentials: "include",
      headers: { Accept: "text/event-stream" },
    }).then((res) => {
      if (!res.ok) throw new Error("Failed to connect to respondent stream");
      return res;
    }),
  llmReport: () => request<LlmReport>("/admin/llm/report"),
  llmLedger: () => request<LlmLedger>("/admin/llm/ledger"),
  llmRunEntries: (runId: string) => request<LlmEntry[]>(`/admin/llm/run/${runId}`),
  llmEvalAccuracy: () => request<EvalAccuracyReport>("/admin/llm/eval-accuracy"),
  adminHealth: () => request<AdminHealthRead>("/admin/health"),
};

