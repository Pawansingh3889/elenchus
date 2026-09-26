import { z } from "zod";
import { useSyncExternalStore } from "react";
import { parsed, request } from "./api";

const count = z.number().int().nonnegative();
const subscribeHash = (changed: () => void) => {
  window.addEventListener("hashchange", changed);
  return () => window.removeEventListener("hashchange", changed);
};
export const useLinkToken = () => useSyncExternalStore(subscribeHash, () => window.location.hash.slice(1), () => "");
const nullableCount = count.nullable();
const status = z.enum(["draft", "published", "closed", "archived"]);
const runStatus = z.enum(["in_progress", "completed", "abandoned"]);
export const answerTypes = ["rating", "yes_no", "single_select", "multi_select", "short_text", "long_text", "number", "date"] as const;
const question = z.object({
  text: z.string(), answer_type: z.enum(answerTypes), options: z.array(z.string()),
  allow_other: z.boolean(), required: z.boolean(),
  follow_up_policy: z.enum(["never", "when_unclear", "always_once"]),
  show_when: z.object({ question: count, op: z.enum(["is", "is_not"]), value: z.string() }).nullable(),
  unit: z.string().nullable(), display_unit: z.string().nullable(),
});
export type Question = z.infer<typeof question>;
const template = z.object({
  id: z.string(), title: z.string(), description: z.string().nullable(), setting: z.string().nullable(),
  audience: z.string(), audience_user_id: z.string().nullable(), status,
  questions: z.array(question.extend({ id: z.string(), position: count })),
});
export type Template = z.infer<typeof template>;
export type Draft = Pick<Template, "title" | "description" | "setting" | "audience" | "audience_user_id"> & { questions: Question[] };
export const blankQuestion = (): Question => ({ text: "", answer_type: "rating", options: [], allow_other: false, required: true, follow_up_policy: "when_unclear", show_when: null, unit: null, display_unit: null });
const access = z.object({
  workspace_id: z.string(), company: z.string(), mode: z.enum(["standard", "demo", "customer"]),
  active: z.boolean(), expires_at: z.string().nullable(), surveys_created: count,
  survey_limit: nullableCount, question_limit: nullableCount, session_limit_per_survey: nullableCount,
  monthly_response_allowance: nullableCount, sessions_started_this_month: count, product: z.string().nullable(),
});
export type Access = z.infer<typeof access>;
const pass = z.object({ workspace_id: z.string(), pass_token: z.string(), expires_at: z.string().nullable() });
const entered = z.object({
  user: z.object({ id: z.string(), display_name: z.string(), email: z.string(), function: z.string().nullable(), band: z.string().nullable(), may_author: z.boolean() }),
  template_id: z.string().nullable(), run_id: z.string().nullable(),
});
const dashboardRow = z.object({
  id: z.string(), title: z.string(), status, started: count, completed: count, in_progress: count,
  abandoned: count, completion_rate: z.number().nullable(), updated_at: z.string(),
});
const tally = z.object({ label: z.string(), count, write_in: z.boolean() });
const report = z.object({
  template_id: z.string(), title: z.string(), runs_total: count, runs_completed: count,
  questions: z.array(z.object({
    id: z.string(), position: count, text: z.string(), answer_type: z.string(), answered: count,
    declined: count, counts: z.array(tally), selections: count, average: z.number().nullable(),
    low: z.number().nullable(), high: z.number().nullable(), verbatim: z.array(z.string()),
    follow_ups: z.array(z.string()), probed: count, unit: z.string().nullable(),
  })),
});
const answer = z.object({ question_id: z.string(), question_text: z.string(), kind: z.enum(["scripted", "follow_up"]), value: z.record(z.string(), z.unknown()), answered_at: z.string() });
const matrix = z.object({
  template_id: z.string(), title: z.string(),
  questions: z.array(z.object({ id: z.string(), position: count, text: z.string(), answer_type: z.string(), options: z.array(z.string()) })),
  runs: z.array(z.object({ run_id: z.string(), respondent_label: z.string(), status: runStatus, started_at: z.string(), completed_at: z.string().nullable(), answers: z.array(answer) })),
});
export type Matrix = z.infer<typeof matrix>;
const finding = z.object({ statement: z.string(), question_position: count.nullable(), question_text: z.string().nullable(), answered: nullableCount, counts: z.array(z.object({ label: z.string(), count })), average: z.number().nullable() });
const recap = z.object({ headline: z.string(), findings: z.array(finding), suggestions: z.array(finding), proposed_actions: z.array(z.object({ action: z.string(), question_position: count.nullable() })), caveat: z.string(), runs_included: count, generated_at: z.string() });
const operator = z.object({
  month: z.string(), budget_usd: z.number(), charged_or_reserved_usd: z.number(), known_spend_usd: z.number(),
  uncertain_attempts: count, attempts: count, failed_attempts: count,
  workspaces: z.array(z.object({ workspace_id: z.string(), company: z.string(), email: z.string(), issued_at: z.string(), activated_at: z.string().nullable(), access })),
});
export type Activation = { product: string; purchase_type: "subscription" | "one_time"; valid_until: string | null; monthly_response_allowance: number; purchase_verified: true };
const post = (body?: unknown): RequestInit => ({ method: "POST", ...(body === undefined ? {} : { body: JSON.stringify(body) }) });

export const demo = {
  options: () => parsed("/demo/options", z.object({ enabled: z.boolean() })),
  enter: (token: string) => parsed("/demo/enter", entered, post({ token })),
  access: () => parsed("/demo/access", access),
  preview: (token: string) => parsed("/demo/survey-preview", z.object({ title: z.string(), description: z.string().nullable(), questions: count, remaining_sessions: nullableCount, disclosure: z.string() }), post({ token })),
  participate: (token: string) => parsed("/demo/survey-enter", entered, post({ token, consent: true })),
  share: (id: string) => parsed(`/demo/surveys/${id}/share`, z.object({ token: z.string(), expires_at: z.string() }), post()),
  dashboard: () => parsed("/dashboard", z.array(dashboardRow)),
  template: (id: string) => parsed(`/templates/${id}`, template),
  create: (draft: Draft) => parsed("/templates", template, post(draft)),
  generate: (prompt: string) => parsed("/templates/generate", z.object({ template, note: z.string() }), post({ prompt, audience: "signed_in" })),
  update: (id: string, draft: Draft) => parsed(`/templates/${id}`, template, { method: "PUT", body: JSON.stringify(draft) }),
  publish: (id: string) => parsed(`/templates/${id}/publish`, template, post()),
  close: (id: string) => parsed(`/templates/${id}/close`, template, post()),
  remove: (id: string) => request<void>(`/templates/${id}`, { method: "DELETE" }),
  report: (id: string) => parsed(`/templates/${id}/report`, report),
  matrix: (id: string) => parsed(`/templates/${id}/answers`, matrix),
  storedRecap: (id: string) => parsed(`/templates/${id}/summary`, z.object({ recap: recap.nullable(), absence: z.enum(["never_generated", "outdated"]).nullable() })),
  summarise: (id: string) => parsed(`/templates/${id}/summary`, recap, post()),
  run: (id: string, run: string) => parsed(`/templates/${id}/runs/${run}`, z.object({ respondent_label: z.string(), status: runStatus, messages: z.array(z.object({ role: z.enum(["assistant", "user"]), content: z.string() })), answers: z.array(answer) })),
  operator: () => parsed("/demo/operator", operator),
  issue: (data: { company: string; name: string; email: string }) => parsed("/demo/passes", pass, post(data)),
  activate: (id: string, data: Activation) => parsed(`/demo/workspaces/${id}/activate`, pass, post(data)),
  revoke: (id: string) => request<void>(`/demo/workspaces/${id}/revoke`, post()),
};

export function exportAnswers(data: Matrix) {
  const rows: unknown[][] = [["Participant", "Status", "Question", "Kind", "Recorded answer", "Answered at"]];
  for (const run of data.runs) for (const answer of run.answers) rows.push([run.respondent_label, run.status, answer.question_text, answer.kind, JSON.stringify(answer.value), answer.answered_at]);
  const csv = rows.map(row => row.map(value => {
    let text = String(value);
    if (/^[\s]*[=+@-]/.test(text) || /^[\t\r\n]/.test(text)) text = "'" + text;
    return '"' + text.replaceAll('"', '""') + '"';
  }).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `survey-${data.template_id}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
