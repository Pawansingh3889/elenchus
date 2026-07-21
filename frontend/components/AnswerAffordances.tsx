"use client";

import { useState } from "react";

import type { CurrentQuestion } from "@/lib/types";

/**
 * Answer controls that appear with the current question. They are shortcuts, not the
 * contract: everything they produce is ordinary text the engine still validates.
 */
export function AnswerAffordances({
  question,
  disabled,
  onAnswer,
}: {
  question: CurrentQuestion;
  disabled: boolean;
  onAnswer: (text: string) => void;
}) {
  const [picked, setPicked] = useState<string[]>([]);
  const [typed, setTyped] = useState("");

  if (question.answer_type === "yes_no") {
    return (
      <div className="afford">
        {["Yes", "No"].map((option) => (
          <button
            key={option}
            className="chip"
            disabled={disabled}
            onClick={() => onAnswer(option)}
          >
            {option}
          </button>
        ))}
      </div>
    );
  }

  if (question.answer_type === "single_select") {
    return (
      <div className="afford">
        {question.options.map((option) => (
          <button
            key={option}
            className="chip"
            disabled={disabled}
            onClick={() => onAnswer(option)}
          >
            {option}
          </button>
        ))}
        {question.allow_other ? (
          <span className="chip chip-dashed afford-hint">or say it in your own words below</span>
        ) : null}
      </div>
    );
  }

  if (question.answer_type === "multi_select") {
    const toggle = (option: string) =>
      setPicked((current) =>
        current.includes(option) ? current.filter((o) => o !== option) : [...current, option],
      );
    return (
      <div className="afford">
        {question.options.map((option) => (
          <button
            key={option}
            className={picked.includes(option) ? "chip chip-on" : "chip"}
            disabled={disabled}
            onClick={() => toggle(option)}
          >
            {option}
          </button>
        ))}
        <button
          className="btn btn-secondary"
          disabled={disabled || picked.length === 0}
          onClick={() => onAnswer(picked.join(", "))}
        >
          Confirm {picked.length ? `(${picked.length})` : ""}
        </button>
      </div>
    );
  }

  if (question.answer_type === "rating") {
    return (
      <div className="afford">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            className="star"
            disabled={disabled}
            aria-label={`${n} out of 5`}
            onClick={() => onAnswer(String(n))}
          >
            ★
          </button>
        ))}
      </div>
    );
  }

  if (question.answer_type === "date" || question.answer_type === "number") {
    return (
      <div className="afford-inline">
        <input
          className="field"
          type={question.answer_type === "date" ? "date" : "number"}
          value={typed}
          disabled={disabled}
          onChange={(e) => setTyped(e.target.value)}
        />
        <button
          className="btn btn-secondary"
          disabled={disabled || !typed}
          onClick={() => onAnswer(typed)}
        >
          Send
        </button>
      </div>
    );
  }

  return null;
}
