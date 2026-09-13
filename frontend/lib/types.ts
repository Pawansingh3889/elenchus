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

export interface User {
  id: string;
  email: string;
  display_name: string;
  function: JobFunction | null;
  band: Band | null;
  may_author: boolean;
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

export type RunStatus = "in_progress" | "completed" | "abandoned";
export type AnswerKind = "scripted" | "follow_up";
export type MessageRole = "assistant" | "user";

export interface RunMessage {
  role: MessageRole;
  content: string;
  created_at: string;
}

/** A transcript message carrying who produced it.
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
