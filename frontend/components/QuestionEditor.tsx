"use client";

import { useRef } from "react";

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
const labelFor = (t: AnswerType) => TYPES.find((x) => x.value === t)?.label ?? t;

interface Props {
  index: number;
  total: number;
  question: QuestionInput;
  /** The server's last save rejected this question, so mark the card rather than
   *  leaving the author to count down from a message at the top of the page. */
  rejected?: boolean;
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
  rejected = false,
  earlier,
  onChange,
  onRemove,
  onMove,
}: Props) {
  const selectType = isSelect(question.answer_type);
  const optionsOf = (position: number) => earlier[position]?.options ?? [];
  // A select can only ever record one of its own options, so start there. A yes/no
  // question has two answers that are not in an options list, so name one. Everything
  // else is free text and the author types it: the value is left empty and the card is
  // marked incomplete, rather than seeding "" and letting the draft look finished until
  // the server refuses it.
  const defaultValueFor = (position: number) => {
    const options = optionsOf(position);
    if (options.length > 0) return options[0];
    return earlier[position]?.answer_type === "yes_no" ? "yes" : "";
  };

  // A condition that exists but has no value cannot be saved (the server requires one),
  // so say so here, next to the control that fixes it.
  const conditionNeedsValue = Boolean(question.show_when && !question.show_when.value.trim());

  // What the options were before a switch away from a select type. The API refuses
  // options on a non-select question (schemas.py, _check_options), so they cannot simply
  // ride along in the draft; they are held here instead and put back if the author
  // returns. Losing an author's typed options to a mis-click and offering no way back is
  // the whole reason this exists.
  const stashedOptions = useRef<string[]>([]);

  const setType = (t: AnswerType) => {
    const leavingSelect = selectType && !isSelect(t);
    const returningToSelect = !selectType && isSelect(t);

    if (leavingSelect && question.options.length > 0) {
      const count = question.options.length;
      const noun = count === 1 ? "option" : "options";
      const confirmed = window.confirm(
        `Changing this question to ${labelFor(t)} removes its ${count} ${noun}.\n\n` +
          `They will be restored if you change it back before saving.`,
      );
      if (!confirmed) return;
      stashedOptions.current = question.options;
    }

    // Only restore into an empty question: if the author has since typed new options,
    // those are the current intent and the stash is stale.
    const restored =
      returningToSelect && question.options.length === 0 ? stashedOptions.current : question.options;

    onChange({
      answer_type: t,
      options: isSelect(t) ? restored : [],
      allow_other: isSelect(t) ? question.allow_other : false,
    });
  };

  const setOption = (i: number, value: string) =>
    onChange({ options: question.options.map((o, j) => (j === i ? value : o)) });
  const addOption = () => onChange({ options: [...question.options, ""] });
  const removeOption = (i: number) =>
    onChange({ options: question.options.filter((_, j) => j !== i) });

  return (
    <div className={rejected ? "qcard qcard-rejected" : "qcard"}>
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
                      aria-invalid={conditionNeedsValue}
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

          {conditionNeedsValue ? (
            <p className="qcard-warn">
              Type the answer this question depends on, or set it back to “always”. The
              survey cannot be saved while the condition has no answer to match.
            </p>
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
