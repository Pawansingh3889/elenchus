"use client";

import type { AnswerType, QuestionInput } from "@/lib/types";

const TYPES: { value: AnswerType; label: string }[] = [
  { value: "single_select", label: "Single select" },
  { value: "multi_select", label: "Multi select" },
  { value: "yes_no", label: "Yes / No" },
  { value: "short_text", label: "Short text" },
  { value: "long_text", label: "Long text" },
  { value: "rating", label: "Rating (1–5)" },
  { value: "number", label: "Number" },
  { value: "date", label: "Date" },
];

const SELECT_TYPES: AnswerType[] = ["single_select", "multi_select"];
const isSelect = (t: AnswerType) => SELECT_TYPES.includes(t);

interface Props {
  index: number;
  total: number;
  question: QuestionInput;
  onChange: (patch: Partial<QuestionInput>) => void;
  onRemove: () => void;
  onMove: (dir: number) => void;
}

export function QuestionEditor({ index, total, question, onChange, onRemove, onMove }: Props) {
  const selectType = isSelect(question.answer_type);

  const setType = (t: AnswerType) =>
    onChange({
      answer_type: t,
      options: isSelect(t) ? question.options : [],
      allow_other: isSelect(t) ? question.allow_other : false,
    });

  const setOption = (i: number, value: string) =>
    onChange({ options: question.options.map((o, j) => (j === i ? value : o)) });
  const addOption = () => onChange({ options: [...question.options, ""] });
  const removeOption = (i: number) =>
    onChange({ options: question.options.filter((_, j) => j !== i) });

  return (
    <div className="qcard">
      <div className="qcard-top">
        <div className="qcard-num">{index + 1}</div>
        <div className="qcard-body">
          <input
            className="field"
            placeholder="Question text"
            value={question.text}
            onChange={(e) => onChange({ text: e.target.value })}
          />
          <div className="qcard-row">
            <select
              className="field"
              value={question.answer_type}
              onChange={(e) => setType(e.target.value as AnswerType)}
            >
              {TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          {selectType ? (
            <div className="options">
              {question.options.map((o, i) => (
                <div className="option-row" key={i}>
                  <input
                    placeholder={`Option ${i + 1}`}
                    value={o}
                    onChange={(e) => setOption(i, e.target.value)}
                  />
                  <button
                    className="icon-btn"
                    onClick={() => removeOption(i)}
                    aria-label="Remove option"
                  >
                    ×
                  </button>
                </div>
              ))}
              <button className="add-dashed" onClick={addOption}>
                + Add option
              </button>
            </div>
          ) : null}

          <div className="qcard-flags">
            <label>
              <input
                type="checkbox"
                checked={question.required}
                onChange={(e) => onChange({ required: e.target.checked })}
              />
              Required
            </label>
            <label>
              <input
                type="checkbox"
                checked={question.allow_follow_ups}
                onChange={(e) => onChange({ allow_follow_ups: e.target.checked })}
              />
              Allow follow-ups
            </label>
            {selectType ? (
              <label>
                <input
                  type="checkbox"
                  checked={question.allow_other}
                  onChange={(e) => onChange({ allow_other: e.target.checked })}
                />
                Allow &ldquo;other&rdquo;
              </label>
            ) : null}
          </div>
        </div>
        <div className="qcard-controls">
          <button
            className="icon-btn"
            onClick={() => onMove(-1)}
            disabled={index === 0}
            aria-label="Move up"
          >
            ↑
          </button>
          <button
            className="icon-btn"
            onClick={() => onMove(1)}
            disabled={index === total - 1}
            aria-label="Move down"
          >
            ↓
          </button>
          <button className="icon-btn" onClick={onRemove} aria-label="Delete question">
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}
