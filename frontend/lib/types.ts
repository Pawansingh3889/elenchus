export type AnswerType =
  | "single_select"
  | "multi_select"
  | "yes_no"
  | "short_text"
  | "long_text"
  | "rating"
  | "number"
  | "date";

export type TemplateStatus = "draft" | "published" | "archived";
export type UserRole = "author" | "respondent";

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: UserRole;
}

export interface QuestionInput {
  text: string;
  answer_type: AnswerType;
  options: string[];
  allow_other: boolean;
  required: boolean;
  allow_follow_ups: boolean;
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
  questions: Question[];
}

export interface TemplateSummary {
  id: string;
  title: string;
  description: string | null;
  status: TemplateStatus;
  updated_at: string;
  question_count: number;
}

// A drafted or refined template plus the model's short note on what it did.
export interface GeneratedTemplate {
  template: Template;
  note: string;
}

export interface TemplateWrite {
  title: string;
  description?: string | null;
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
  summary: StoredRunSummary | null;
}
