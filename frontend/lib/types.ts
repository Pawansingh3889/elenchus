export type AnswerType =
  | "single_select"
  | "multi_select"
  | "yes_no"
  | "short_text"
  | "long_text"
  | "rating"
  | "number"
  | "date";

/** Whether the interviewer probes this question, and how hard. `when_unclear` is what
 *  the old `allow_follow_ups` boolean bought; `always_once` is the one it could not say,
 *  and the engine enforces it by withholding the ways past the question. */
export type FollowUpPolicy = "never" | "when_unclear" | "always_once";

export type TemplateStatus = "draft" | "published" | "closed" | "archived";
/** Who a survey is for: the whole respondent pool, or one creator department. */
export type SurveyAudience = "respondents" | "hr" | "operations" | "finance" | "technical";
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
  follow_up_policy: FollowUpPolicy;
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
  audience: SurveyAudience;
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
  /** Who the survey is for. Required on an update, where omitting it used to reset an
   *  HR survey to the whole respondent pool on every save. */
  audience: SurveyAudience;
  /** What the interviewer needs to know about the workplace to read answers here.
   *  Never shown to the respondent. Optional: most surveys need none. */
  setting?: string | null;
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
  /** People rather than runs: how many this survey is for, and how many of them have
   *  opened and finished it. Kept beside the run counts rather than replacing them,
   *  because "how is this going" and "how many of the people it was for have answered"
   *  are different questions. */
  reach: number;
  people_started: number;
  people_completed: number;
  last_started_at: string | null;
  last_completed_at: string | null;
  completion_rate: number | null;
  /** Of the people this survey is for, how many finished. Null when it is aimed at
   *  nobody. Can exceed 1: an author testing their own survey answers it without being
   *  in its audience, which is reported rather than hidden. */
  response_rate: number | null;
}

/** One row of a select question's tally. `label` is the option as the author wrote it,
 *  or the respondent's own words for a write-in. */
export interface OptionCount {
  label: string;
  count: number;
  write_in: boolean;
}

/** One question, as the whole survey answered it. `answered` and `declined` are apart
 *  because a question everyone skipped and one nobody reached are different findings. */
export interface QuestionReport {
  id: string;
  position: number;
  text: string;
  answer_type: AnswerType;
  answered: number;
  declined: number;
  counts: OptionCount[];
  /** Ratings and numbers only. Null when nobody answered, not 0. */
  average: number | null;
  /** Free text and write-ins, verbatim and in full. Counted on the page, shown on click. */
  verbatim: string[];
  /** What the probes drew out. Never in `counts` or `average`: a follow-up answers a
   *  question the model wrote, so it belongs to no option list and no scale. */
  follow_ups: string[];
  /** Runs probed on this question, not probes asked, so it reads against `answered`. */
  probed: number;
}

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

export interface SurveyQuote {
  question: string;
  respondent: string;
  quote: string;
}

/** The recap of a whole survey. `runs_included` is what it was written from, shown on
 *  the page because a recap is only true of the responses it read. */
export interface SurveySummary {
  headline: string;
  findings: SurveyFinding[];
  notable_quotes: SurveyQuote[];
  version: number;
  runs_included: number;
  generated_at: string;
}

export interface SurveyReport {
  template_id: string;
  title: string;
  version: number;
  runs_total: number;
  runs_completed: number;
  reach: number;
  people_started: number;
  people_completed: number;
  /** Answered against an earlier published version, so counted apart rather than folded
   *  in: their questions are not these questions. */
  runs_on_earlier_versions: number;
  questions: QuestionReport[];
}
