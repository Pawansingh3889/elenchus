"use client";

import type { AnswerType, QuestionInput, ShowWhenOp } from "@/lib/types";

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
  /** Every question before this one — what a condition may reference. */
  earlier: QuestionInput[];
  onChange: (patch: Partial<QuestionInput>) => void;
  onRemove: () => void;
  onMove: (dir: number) => void;
}

export function QuestionEditor({
  index,
  total,
  question,
  earlier,
  onChange,
  onRemove,
  onMove,
}: Props) {
  const selectType = isSelect(question.answer_type);
  const optionsOf = (position: number) => earlier[position]?.options ?? [];
  // A select can only ever record one of its own options, so start there; anything else
  // is free text and the author types it.
  const defaultValueFor = (position: number) => optionsOf(position)[0] ?? "";

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

          {/* Only questions with something before them can be conditional — the engine
              decides visibility from answers already recorded, so a condition on a later
              question could never come true. */}
          {index > 0 ? (
            <div className="qcard-visibility">
              <span className="qcard-vis-label">Show</span>
              <select
                value={question.show_when ? "cond" : "always"}
                onChange={(e) =>
                  onChange({
                    show_when:
                      e.target.value === "cond"
                        ? { question: index - 1, op: "is", value: defaultValueFor(index - 1) }
                        : null,
                  })
                }
              >
                <option value="always">always</option>
                <option value="cond">only if…</option>
              </select>

              {question.show_when ? (
                <>
                  <select
                    value={question.show_when.question}
                    onChange={(e) => {
                      const target = Number(e.target.value);
                      onChange({
                        show_when: {
                          ...question.show_when!,
                          question: target,
                          // The old value belongs to a different question's options.
                          value: defaultValueFor(target),
                        },
                      });
                    }}
                  >
                    {earlier.map((q, i) => (
                      <option key={i} value={i}>
                        Q{i + 1}: {q.text.slice(0, 28) || "(untitled)"}
                      </option>
                    ))}
                  </select>

                  <select
                    value={question.show_when.op}
                    onChange={(e) =>
                      onChange({
                        show_when: { ...question.show_when!, op: e.target.value as ShowWhenOp },
                      })
                    }
                  >
                    <option value="is">is</option>
                    <option value="is_not">is not</option>
                  </select>

                  {/* A select's answer can only ever be one of its options, so offer
                      those rather than letting the author mistype one. */}
                  {optionsOf(question.show_when.question).length > 0 ? (
                    <select
                      value={question.show_when.value}
                      onChange={(e) =>
                        onChange({
                          show_when: { ...question.show_when!, value: e.target.value },
                        })
                      }
                    >
                      {optionsOf(question.show_when.question).map((o) => (
                        <option key={o} value={o}>
                          {o}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      value={question.show_when.value}
                      placeholder="answer"
                      onChange={(e) =>
                        onChange({
                          show_when: { ...question.show_when!, value: e.target.value },
                        })
                      }
                    />
                  )}
                </>
              ) : null}
            </div>
          ) : null}
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
