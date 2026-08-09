"use client";

import { AnswerTypePolicy } from "@/components/AnswerTypePolicy";
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
 * Shut by default. They are set once and rarely revisited, and as three open cards they
 * cost the height of the first two questions on every visit to a page whose job is
 * editing questions. A `details` element rather than state and a chevron, so the
 * disclosure is keyboard and screen-reader accessible without any of that being
 * reimplemented here.
 *
 * Presentational: the state stays on the page, because the save body is assembled there
 * and a setting held here would have to be lifted straight back.
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

  // What the panel says while it is shut. A panel that hides what it holds is worse than
  // one that takes the room, so closed it still reports who the survey is for, whether
  // the answer types are restricted, and whether a setting was written.
  const summary = [
    AUDIENCES.find((a) => a.value === audience)?.label ?? audience,
    allowedTypes.length ? msg.builder.typesSome(allowedTypes.length) : msg.builder.typesAll,
    ...(setting.trim() ? [msg.builder.settingWritten] : []),
  ].join(" · ");

  return (
    <details className="card settings-panel">
      <summary>
        <span className="card-label">{msg.builder.settingsTitle}</span>
        <span className="muted settings-summary">{summary}</span>
      </summary>

      <div className="settings-body">
        <div className="settings-field">
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

        <div className="settings-field">
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

        <div className="settings-field">
          <div className="card-label">{msg.builder.answerTypesTitle}</div>
          <AnswerTypePolicy
            allowedTypes={allowedTypes}
            onChange={onAllowedTypesChange}
            hint={msg.builder.answerTypesHint}
          />
        </div>
      </div>
    </details>
  );
}
