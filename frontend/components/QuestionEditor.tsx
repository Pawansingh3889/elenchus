"use client";

import { useRef, useState } from "react";

import { ANSWER_TYPES, labelForAnswerType } from "@/lib/answerTypes";
import { AutoGrowTextarea } from "@/components/AutoGrowTextarea";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { useT } from "@/lib/i18n/useT";
import type { AnswerType, FollowUpPolicy, QuestionInput, ShowWhenOp } from "@/lib/types";
import { unitsByDimension, unitDimension } from "@/lib/units";

const SELECT_TYPES: AnswerType[] = ["single_select", "multi_select"];
const isSelect = (t: AnswerType) => SELECT_TYPES.includes(t);
const labelFor = labelForAnswerType;

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
  const msg = useT();
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

  // The type the author has asked for but not yet confirmed, when confirming is needed.
  // `window.confirm` was here, which the app's own ConfirmDialog docstring called out as
  // the last holdout: a native dialog prefixes the page origin ("localhost:3000 says"),
  // which reads as the browser warning about the page rather than as the app asking
  // about the author's own options. It also blocks the whole tab, which is worse here
  // than anywhere else because the warning is about losing typed work.
  const [pendingType, setPendingType] = useState<AnswerType | null>(null);

  const applyType = (t: AnswerType) => {
    const returningToSelect = !selectType && isSelect(t);
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

  const setType = (t: AnswerType) => {
    if (selectType && !isSelect(t) && question.options.length > 0) {
      setPendingType(t);
      return;
    }
    applyType(t);
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
          <AutoGrowTextarea
            placeholder={msg.builder.questionPlaceholder}
            value={question.text}
            onChange={(text) => onChange({ text })}
          />
          <div className="qcard-row">
            <select
              className="field"
              value={question.answer_type}
              onChange={(e) => setType(e.target.value as AnswerType)}
            >
              {ANSWER_TYPES.map((t) => (
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
                  {/* No "field" class: option rows carry their own compact styling via
                      the `.option-row textarea` rule, so the shared field chrome would
                      double the borders and padding. */}
                  <AutoGrowTextarea
                    className=""
                    placeholder={msg.builder.optionPlaceholder(i + 1)}
                    value={o}
                    onChange={(value) => setOption(i, value)}
                  />
                  <button
                    className="icon-btn"
                    onClick={() => removeOption(i)}
                    aria-label={msg.builder.removeOption}
                  >
                    ×
                  </button>
                </div>
              ))}
              <button className="add-dashed" onClick={addOption}>
                {msg.builder.addOption}
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
              {msg.builder.required}
            </label>
            {/* A select rather than a checkbox, because the third value is the point.
                A tick could only ever say "probing allowed", which the interviewer reads
                as "probe if the answer is unusable" and then almost never does. */}
            <label>
              {msg.builder.followUps}
              <select
                value={question.follow_up_policy}
                onChange={(e) =>
                  onChange({ follow_up_policy: e.target.value as FollowUpPolicy })
                }
              >
                <option value="never">{msg.builder.followUpsNever}</option>
                <option value="when_unclear">{msg.builder.followUpsWhenUnclear}</option>
                <option value="always_once">{msg.builder.followUpsAlwaysOnce}</option>
              </select>
            </label>
            {selectType ? (
              <label>
                <input
                  type="checkbox"
                  checked={question.allow_other}
                  onChange={(e) => onChange({ allow_other: e.target.checked })}
                />
                {msg.builder.allowOther}
              </label>
            ) : null}
          </div>

          {/* A measured number is meaningless without its unit — the case that put "the
              temperature question had no unit" on the list. Only offered for number
              questions; the optional second unit lets an author show, say, °F alongside
              a Celsius reading. Plain English labels: these are new fields and not yet in
              the translation catalog. */}
          {question.answer_type === "number" ? (
            <div className="qcard-row">
              <label>
                Unit
                <select
                  value={question.unit ?? ""}
                  onChange={(e) => onChange({ unit: e.target.value || null })}
                >
                  <option value="">None</option>
                  {Object.entries(unitsByDimension()).map(([dim, choices]) => (
                    <optgroup key={dim} label={dim}>
                      {choices.map((c) => (
                        <option key={c.value} value={c.value}>
                          {c.label}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </label>
              {question.unit ? (
                <label>
                  Also show in
                  <select
                    value={question.display_unit ?? ""}
                    onChange={(e) => onChange({ display_unit: e.target.value || null })}
                  >
                    <option value="">—</option>
                    {(() => {
                      const dim = unitDimension(question.unit);
                      const choices = dim ? unitsByDimension()[dim] : [];
                      return choices.map((c) => (
                        <option key={c.value} value={c.value}>
                          {c.label}
                        </option>
                      ));
                    })()}
                  </select>
                </label>
              ) : null}
            </div>
          ) : null}

          {/* Only questions with something before them can be conditional — the engine
              decides visibility from answers already recorded, so a condition on a later
              question could never come true. */}
          {index > 0 ? (
            <div className="qcard-visibility">
              <span className="qcard-vis-label">{msg.builder.show}</span>
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
                <option value="always">{msg.builder.always}</option>
                <option value="cond">{msg.builder.onlyIf}</option>
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
                    <option value="is">{msg.builder.is}</option>
                    <option value="is_not">{msg.builder.isNot}</option>
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
                      placeholder={msg.builder.answerPlaceholder}
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
            <p className="qcard-warn">{msg.builder.conditionNeedsValue}</p>
          ) : null}
        </div>
        <div className="qcard-controls">
          <button
            className="icon-btn"
            onClick={() => onMove(-1)}
            disabled={index === 0}
            aria-label={msg.builder.moveUp}
          >
            ↑
          </button>
          <button
            className="icon-btn"
            onClick={() => onMove(1)}
            disabled={index === total - 1}
            aria-label={msg.builder.moveDown}
          >
            ↓
          </button>
          <button className="icon-btn" onClick={onRemove} aria-label={msg.builder.removeQuestion}>
            ✕
          </button>
        </div>
      </div>

      {pendingType ? (
        <ConfirmDialog
          title={msg.builder.typeChangeTitle}
          confirmLabel={msg.builder.typeChangeConfirm}
          cancelLabel={msg.common.cancel}
          danger
          onConfirm={() => {
            // Stash before applying, so returning to a select puts the options back.
            stashedOptions.current = question.options;
            applyType(pendingType);
            setPendingType(null);
          }}
          onCancel={() => setPendingType(null)}
        >
          <p>{msg.builder.typeChangeWarning(labelFor(pendingType), question.options.length)}</p>
        </ConfirmDialog>
      ) : null}
    </div>
  );
}
