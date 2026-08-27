/**
 * Shapes that are validated at runtime live in `schemas.ts` and are inferred from the
 * zod schema there, so there is one definition rather than a type here and a checker
 * elsewhere quietly disagreeing with it. They are re-exported so every existing import
 * of them keeps working unchanged.
 */
import type { AnswerType, OptionCount, TemplateStatus } from "./schemas";

export type {
  AnswerType,
  TemplateStatus,
  OptionCount,
  QuestionReport,
  SurveyReport,
  DashboardRow,
} from "./schemas";

/** Whether the interviewer probes this question, and how hard. `when_unclear` is what
 *  the old `allow_follow_ups` boolean bought; `always_once` is the one it could not say,
 *  and the engine enforces it by withholding the ways past the question. */
export type FollowUpPolicy = "never" | "when_unclear" | "always_once";

/** Who a survey is for: everyone with a job, one slice of the org chart, or one named
 *  person. Membership is derived server-side from each person's job, never stored.
 *  `person` carries its target in `audience_user_id`; the two only mean anything
 *  together, and the API refuses either half on its own. */
export type SurveyAudience =
  | "everyone"
  | "operatives"
  | "line_leaders"
  | "supervisors"
  | "shift_managers"
  | "managers"
  | "qa"
  | "health_safety"
  | "person";
/** Which ladder somebody is on. `JobFunction` rather than `Function`, which is a
 *  global type in TypeScript and shadowing it invites quiet breakage. `it` also
 *  grants admin. */
export type JobFunction =
  | "production"
  | "quality"
  | "health_safety"
  | "technical"
  | "planning"
  | "hr"
  | "finance"
  | "supply_chain"
  | "it"
  | "executive";
/** How high on the ladder. Ordered on the server; manager and up may author. The
 *  order is deliberately not re-derived here: `may_author` arrives computed. */
export type Band =
  | "operative"
  | "line_leader"
  | "supervisor"
  | "manager"
  | "head"
  | "director";
/** A cross-cutting responsibility on top of the job. */
export type Hat = "health_safety";

/** One person as the directory shows them. Deliberately no email: a name and a job
 *  answer "who is in this audience", and an address is contactable data the page has
 *  no use for. A null job is a service account: in no audience at all. */
export interface Person {
  id: string;
  display_name: string;
  function: JobFunction | null;
  band: Band | null;
  hats: Hat[];
  /** Derived server-side from the band, so the page never re-invents the cutoff. */
  may_author: boolean;
  /** Whether this account carries an Entra object id, not the id itself. Somebody at
   *  an authoring band without one builds surveys today and has no way to sign in
   *  when the header shim is replaced, so the directory marks it. */
  has_microsoft_id: boolean;
  /** Which audiences reach this person, computed server-side by `app/access`. The
   *  browser must not re-derive this: a map of who a survey reaches, drawn from a
   *  paraphrase of the rules, is a map that drifts from them. `person` is absent by
   *  construction, being a property of a survey rather than of a job. */
  audiences: SurveyAudience[];
}

/** The caller, as themselves. Both derived flags are the server's to compute:
 *  `may_author` turns on band order, and half of `is_admin` is an email allowlist
 *  that lives in server settings. */
export interface Me {
  id: string;
  display_name: string;
  function: JobFunction | null;
  band: Band | null;
  may_author: boolean;
  is_admin: boolean;
}

/** What an administrator sets on an account: the job, both halves required, plus any
 *  hats. There is no role field; what the account may do derives from these. The
 *  update is a full replacement rather than a patch, so the form sends everything. */
export interface AccountWrite {
  display_name: string;
  function: JobFunction;
  band: Band;
  microsoft_id: string | null;
  hats: Hat[];
}

/** Creating adds the address. There is no way to change one afterwards: `is_admin`
 *  matches its allowlist on the email, so editing it would be a way to hand somebody
 *  administration through a field that looks like a typo correction. */
export type AccountCreate = AccountWrite & { email: string };

export interface Account {
  id: string;
  email: string;
  display_name: string;
  function: JobFunction | null;
  band: Band | null;
  microsoft_id: string | null;
  created_by: string | null;
  hats: Hat[];
}

/** How many people each audience is, right now. Live by decision: the count follows
 *  the org chart as jobs change. `person` is absent, not zero; its reach is one by
 *  definition and the screen already names the person. */
export type AudienceReach = Record<Exclude<SurveyAudience, "person">, number>;

/** One audit row. `changed_by_name` is null when the editor's account is gone; the row
 *  outlives them on purpose. `before`/`after` arrive as the plain JSON the row stores:
 *  the log is append-only and outlives vocabularies, so rows written before the job
 *  model say `role`, `department` and `groups`, and the screen renders whichever keys
 *  a row carries rather than the server rewriting history into today's shape. */
export interface AccountChangeEntry {
  id: string;
  changed_at: string;
  changed_by: string | null;
  changed_by_name: string | null;
  kind: "created" | "updated";
  before: Record<string, unknown> | null;
  after: Record<string, unknown>;
}

/** One open survey this edit would move the person in or out of. */
export interface SurveyImpact {
  template_id: string;
  title: string;
  audience: SurveyAudience;
  now_in: boolean;
  reach_before: number;
  reach_after: number;
}

/** What saving an edit would change, computed server-side before anything is saved. */
export interface AccountImpact {
  function_before: JobFunction | null;
  function_after: JobFunction;
  band_before: Band | null;
  band_after: Band;
  /** Whether the edit changes who they are to the app, derived where band order
   *  lives. The dialog warns on a flip in either direction. */
  may_author_before: boolean;
  may_author_after: boolean;
  hats_added: Hat[];
  hats_removed: Hat[];
  surveys: SurveyImpact[];
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  function: JobFunction | null;
  band: Band | null;
  may_author: boolean;
}

export type ShowWhenOp = "is" | "is_not";

/** A question's visibility condition. `question` is the 0-based **position** of an
 *  earlier question, not its id — a draft save replaces every question row, so ids do
 *  not survive an edit. Positions shift when questions move, so anything that reorders
 *  or deletes must remap these (see remapConditions in the builder). */
export interface ShowWhen {
  question: number;
  op: ShowWhenOp;
  value: string;
}

export interface QuestionInput {
  text: string;
  answer_type: AnswerType;
  options: string[];
  allow_other: boolean;
  required: boolean;
  follow_up_policy: FollowUpPolicy;
  show_when: ShowWhen | null;
  /** The unit a numeric answer is in, and an optional second unit to also display. */
  unit?: string | null;
  display_unit?: string | null;
}

export interface Question extends QuestionInput {
  id: string;
  position: number;
}

export interface Template {
  id: string;
  title: string;
  description: string | null;
  status: TemplateStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
  audience: SurveyAudience;
  /** The one person, when `audience` is `person`, and null otherwise. */
  audience_user_id: string | null;
  setting: string | null;
  questions: Question[];
}

/** An unfinished run offered back to the respondent who started it. */
export interface ResumableRun {
  id: string;
  template_id: string;
  title: string;
  answered: number;
  total: number;
  started_at: string;
  /** True when an author has asked this run to clarify an answer and no reply has come. */
  pending_clarification: boolean;
}

export interface TemplateSummary {
  id: string;
  title: string;
  description: string | null;
  status: TemplateStatus;
  updated_at: string;
  question_count: number;
  /** Only set on the published list a respondent chooses from. */
  estimated_minutes: number | null;
  /** This reader has already completed it. Only ever true on that same published list. */
  answered?: boolean;
}

// A drafted or refined template plus the model's short note on what it did.
export interface GeneratedTemplate {
  template: Template;
  note: string;
}

export interface TemplateWrite {
  title: string;
  description?: string | null;
  /** Who the survey is for. Required on an update, where omitting it used to reset a
   *  targeted survey to the whole floor on every save. */
  audience: SurveyAudience;
  /** Rides with `audience` on every write. A save that carries `person` without this
   *  is a 422, and one that carries this without `person` is too: the server refuses
   *  either half alone rather than storing a survey aimed at nobody. */
  audience_user_id?: string | null;
  /** What the interviewer needs to know about the workplace to read answers here.
   *  Never shown to the respondent. Optional: most surveys need none. */
  setting?: string | null;
  questions: QuestionInput[];
}

export type RunStatus = "in_progress" | "completed" | "abandoned";
export type AnswerKind = "scripted" | "follow_up";
export type MessageRole = "assistant" | "user";

export interface RunMessage {
  role: MessageRole;
  content: string;
  created_at: string;
}

/** A transcript message as the *author* receives it, carrying who produced it.
 *
 *  Separate from RunMessage because the respondent's own chat payload does not include
 *  these: which provider conducted their interview is not theirs to be told. All three
 *  are optional because the columns are: their own messages and the engine's opening
 *  line were written by nobody's model, and anything recorded before the columns existed
 *  has no provenance to report rather than a default one. */
export interface RunMessageDetail extends RunMessage {
  prompt_version?: string | null;
  model?: string | null;
  tier?: number | null;
}

export interface RunAnswer {
  question_id: string;
  kind: AnswerKind;
  question_text: string;
  value: Record<string, unknown>;
  answered_at: string;
}

export interface CurrentQuestion {
  id: string;
  text: string;
  answer_type: AnswerType;
  options: string[];
  allow_other: boolean;
  required: boolean;
  unit?: string | null;
  display_unit?: string | null;
}

export interface Run {
  id: string;
  status: RunStatus;
  current_question: CurrentQuestion | null;
  /** The engine is probing: the last question came from the model, so `current_question`
   *  describes the scripted question behind it and not what is actually being asked. */
  awaiting_follow_up: boolean;
  answered: number;
  total: number;
  messages: RunMessage[];
  answers: RunAnswer[];
}

export interface RunSummary {
  id: string;
  respondent_label: string;
  status: RunStatus;
  answered: number;
  total: number;
  started_at: string;
  completed_at: string | null;
}

export interface RunQuote {
  question: string;
  quote: string;
}

/** The AI summary of one completed run. Quotes are verbatim: the backend drops any the
 *  respondent did not actually say, so what arrives here can be shown as their words. */
export interface RunSummaryContent {
  headline: string;
  key_facts: string[];
  notable_quotes: RunQuote[];
}

/** As stored on the run: the content plus the provenance the API adds when writing it. */
export type StoredRunSummary = RunSummaryContent & {
  prompt_version?: string;
  generated_at?: string;
};

export interface RunDetail {
  id: string;
  respondent_label: string;
  status: RunStatus;
  started_at: string;
  completed_at: string | null;
  messages: RunMessageDetail[];
  answers: RunAnswer[];
  /** Follow-ups the engine issued, keyed by question id. A probe is charged when it is
   *  asked, and one that draws out the scripted answer leaves no follow-up answer — so
   *  this is the only place a probed question shows up as probed. */
  follow_ups_asked: Record<string, number>;
  summary: StoredRunSummary | null;
}


/** One row of a select question's tally. `label` is the option as the author wrote it,
 *  or the respondent's own words for a write-in. */


/** One thing the survey found. `statement` carries no figures by design: the model
 *  names the pattern, and the counts beside it are attached from the report, so a
 *  number on this page can never be one the model wrote. */
export interface SurveyFinding {
  statement: string;
  question_position: number | null;
  question_text: string | null;
  answered: number | null;
  counts: OptionCount[];
  average: number | null;
}

/** The recap of a whole survey: a fixed short shape, one headline, at most three
 *  findings, at most three suggestions, and a caveat line. `runs_included` is what it
 *  was written from, shown on the page because a recap is only true of the responses it
 *  read. */
export interface SurveySummary {
  headline: string;
  findings: SurveyFinding[];
  /** What a respondent proposed doing about it, not the model's own idea of a fix.
   *  Same shape and same grounding as `findings`: no figures, and a suggestion the
   *  verifier could not trace to something a respondent actually wrote is dropped
   *  before it reaches here. Empty when nobody proposed anything, which is correct
   *  rather than a gap to fill. */
  suggestions: SurveyFinding[];
  /** The evidence line, computed server-side from the report (who answered, earlier
   *  versions, mostly-declined questions). Engine numbers, never model prose. */
  caveat: string;
  runs_included: number;
  generated_at: string;
  /** Which prompt and which tier wrote it. Optional because a recap stored before these
   *  were recorded has none, and that is a fact about the document rather than a gap. */
  prompt_version?: string | null;
  verify_prompt_version?: string | null;
  model?: string | null;
}

/** Why there is no recap to show, when there is none.
 *
 *  Two absences rather than one null, because the page says different things about
 *  them: `never_generated` offers a first recap, `outdated` says the responses have
 *  moved past the one that exists. */
export type RecapAbsence = "never_generated" | "outdated";

export interface SurveyRecapStatus {
  recap: SurveySummary | null;
  absence: RecapAbsence | null;
}

export interface MatrixQuestion {
  id: string;
  position: number;
  text: string;
  answer_type: AnswerType;
  options: string[];
}

export interface MatrixRun {
  run_id: string;
  respondent_label: string;
  status: RunStatus;
  started_at: string;
  completed_at: string | null;
  answers: RunAnswer[];
}

/** Every answer to this survey, by respondent, with nothing tallied.
 *
 *  This is what makes a slice possible: the report can say what a question found but
 *  not whether the people who said one thing also said another, and reconstructing
 *  that from the per-run endpoint took one request per response. */
export interface AnswersMatrix {
  template_id: string;
  title: string;
  questions: MatrixQuestion[];
  runs: MatrixRun[];
}


/** One respondent's participation in a survey, for the dashboard with real-time status. */
export interface RespondentRow {
  respondent_id: string;
  respondent_label: string;
  display_name: string;
  total_runs: number;
  completed_runs: number;
  in_progress_runs: number;
  abandoned_runs: number;
  first_started_at: string;
  last_started_at: string;
  last_completed_at: string | null;
  /** Real-time session status */
  current_run_id: string | null;
  current_status: RunStatus | null;
  last_activity_at: string | null;
}

export interface LlmModelStats {
  model: string;
  tier: number | null;
  calls: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_context_tokens: number;
  avg_latency_ms: number;
  error_count: number;
}

export interface LlmRunSummary {
  run_id: string | null;
  model: string;
  tier: number | null;
  calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  context_tokens: number;
  avg_latency_ms: number;
  error_count: number;
  first_ts: string;
  last_ts: string;
  ops: string[];
}

export interface LlmOpStats {
  op: string;
  calls: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_context_tokens: number;
  avg_latency_ms: number;
  error_count: number;
  source_files: string[];
}

export interface LlmReport {
  total_entries: number;
  total_runs: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_context_tokens: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  models: LlmModelStats[];
  runs: LlmRunSummary[];
  ops: LlmOpStats[];
}

/** The judge's verdicts on the captured live-run corpus (backend/tests/live_runs/),
 *  not live production traffic. See app.llm.eval_corpus on the backend. */
export interface EvalAnswerTypeStats {
  answer_type: string;
  total_answers: number;
  judged: number;
  flagged: number;
  known_inventions: number;
}

export interface EvalAccuracyReport {
  total_fixtures: number;
  total_answers: number;
  judged: number;
  flagged: number;
  known_inventions: number;
  by_answer_type: EvalAnswerTypeStats[];
}

export interface LlmEntry {
  ts: string;
  op: string | null;
  tier: number | null;
  model: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  context_tokens: number | null;
  latency_ms: number | null;
  status: number | null;
  error: string | null;
  cost_usd: number | null;
  // Code-level transparency: where in the codebase this call originated
  source_file?: string | null;
  source_line?: number | null;
}

export interface AdminHealthRead {
  status: string;
  database: string;
  demo_mode: boolean;
  tiers: Record<string, Record<string, unknown>>;
}

export interface LlmLedgerEntry {
  ts: string;
  run_id: string | null;
  op: string | null;
  prompt: string | null;
  tier: number | null;
  model: string | null;
  params_b: number | null;
  local: boolean | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  context_tokens: number | null;
  latency_ms: number | null;
  status: number | null;
  error: string | null;
  cost_usd: number | null;
  // Code-level transparency: where in the codebase this call originated
  source_file: string | null;
  source_line: number | null;
}

export interface LlmLedger {
  entries: LlmLedgerEntry[];
  total_entries: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_context_tokens: number;
  total_cost_usd: number;
}
