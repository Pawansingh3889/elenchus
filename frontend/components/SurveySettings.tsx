"use client";

import { ANSWER_TYPES } from "@/lib/answerTypes";
import { AUDIENCES } from "@/lib/audiences";
import { useT } from "@/lib/i18n/useT";
import type { AnswerType, SurveyAudience, TemplateStatus } from "@/lib/types";

interface Props {
  /** Who the survey is for. Frozen once published, which is the rule the service
   *  enforces with a 409, so the control is disabled rather than offering that error. */
  audience: SurveyAudience;
  onAudienceChange: (audience: SurveyAudience) => void;
  /** The workplace, written for the AI that conducts the survey. Never shown to a
   *  respondent. Held as a string here and turned into null by the caller when blank. */
  setting: string;
  onSettingChange: (setting: string) => void;
  /** Answer types this survey allows. Empty is every type, not "unset". */
  allowedTypes: AnswerType[];
  onAllowedTypesChange: (types: AnswerType[]) => void;
  status: TemplateStatus;
}

/**
 * The three template-level settings, which belong to the survey rather than to any one
 * question: who it is for, what the interviewer should know, and which answer types it
 * permits.
 *
 * Split out of the builder page because they arrived one at a time and the page was
 * already holding the title, description, question list, condition repair, refine panel
 * and publish flow. Each is presentational: the state stays on the page, because the save
 * body is assembled there and a setting held here would have to be lifted straight back.
 */
export function SurveySettings({
  audience,
  onAudienceChange,
  setting,
  onSettingChange,
  allowedTypes,
  onAllowedTypesChange,
  status,
}: Props) {
  const msg = useT();
  const frozen = status !== "draft";

  const toggleType = (type: AnswerType, allowed: boolean) =>
    onAllowedTypesChange(
      allowed ? [...allowedTypes, type] : allowedTypes.filter((v) => v !== type),
    );

  return (
    <>
      <div className="card types-card">
        <div className="card-label">{msg.builder.audienceTitle}</div>
        <select
          className="field"
          value={audience}
          onChange={(e) => onAudienceChange(e.target.value as SurveyAudience)}
          disabled={frozen}
        >
          {AUDIENCES.map((a) => (
            <option key={a.value} value={a.value}>
              {a.label}
            </option>
          ))}
        </select>
        {frozen ? <p className="muted types-hint">{msg.builder.audienceFrozen}</p> : null}
      </div>

      <div className="card types-card">
        <div className="card-label">{msg.builder.settingTitle}</div>
        <p className="muted types-hint">{msg.builder.settingHint}</p>
        <textarea
          className="field builder-desc"
          value={setting}
          onChange={(e) => onSettingChange(e.target.value)}
          placeholder={msg.builder.settingPlaceholder}
          maxLength={2000}
        />
      </div>

      <div className="card types-card">
        <div className="card-label">{msg.builder.answerTypesTitle}</div>
        <p className="muted types-hint">{msg.builder.answerTypesHint}</p>
        <div className="types-grid">
          {ANSWER_TYPES.map((t) => (
            <label key={t.value}>
              <input
                type="checkbox"
                checked={allowedTypes.includes(t.value)}
                onChange={(e) => toggleType(t.value, e.target.checked)}
              />
              {t.label}
            </label>
          ))}
        </div>
      </div>
    </>
  );
}
