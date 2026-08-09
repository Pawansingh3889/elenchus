export type AnswerType =
  | "single_select"
  | "multi_select"
  | "yes_no"
  | "short_text"
  | "long_text"
  | "rating"
  | "number"
  | "date";

export type TemplateStatus = "draft" | "published" | "closed" | "archived";
export type UserRole = "author" | "respondent";

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: UserRole;
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
  allow_follow_ups: boolean;
  show_when: ShowWhen | null;
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
  allowed_answer_types: AnswerType[];
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
}

// A drafted or refined template plus the model's short note on what it did.
export interface GeneratedTemplate {
  template: Template;
  note: string;
}

export interface TemplateWrite {
  title: string;
  description?: string | null;
  /** The answer types this survey allows. Empty is every type, not "unset".
   *
   *  Must be sent on every save. A write replaces the whole template, so omitting this
   *  clears the policy, which is how "no text questions" kept coming undone. */
  allowed_answer_types: AnswerType[];
  questions: QuestionInput[];
}

export interface TemplateVersion {
  id: string;
  template_id: string;
  version: number;
  published_at: string;
}

export type RunStatus = "in_progress" | "completed" | "abandoned";
export type AnswerKind = "scripted" | "follow_up";
export type MessageRole = "assistant" | "user";

export interface RunMessage {
  role: MessageRole;
  content: string;
  created_at: string;
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
  respondent_name: string;
  status: RunStatus;
  version: number;
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
  respondent_name: string;
  status: RunStatus;
  version: number;
  started_at: string;
  completed_at: string | null;
  messages: RunMessage[];
  answers: RunAnswer[];
  /** Follow-ups the engine issued, keyed by question id. A probe is charged when it is
   *  asked, and one that draws out the scripted answer leaves no follow-up answer — so
   *  this is the only place a probed question shows up as probed. */
  follow_ups_asked: Record<string, number>;
  summary: StoredRunSummary | null;
}

/** One survey on the author's dashboard: what it is, and how it is going.
 *  completion_rate is null rather than 0 when nobody has started, because zero would
 *  read as everyone abandoning. */
export interface DashboardRow {
  id: string;
  title: string;
  status: TemplateStatus;
  updated_at: string;
  closed_at: string | null;
  started: number;
  completed: number;
  in_progress: number;
  abandoned: number;
  last_started_at: string | null;
  last_completed_at: string | null;
  completion_rate: number | null;
}
