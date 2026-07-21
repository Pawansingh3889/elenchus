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
