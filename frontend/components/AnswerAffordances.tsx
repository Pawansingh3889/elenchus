"use client";

import { useState } from "react";

import { useT } from "@/lib/i18n/useT";
import type { CurrentQuestion } from "@/lib/types";

/**
 * Answer controls that appear with the current question. They are shortcuts, not the
 * contract: everything they produce is ordinary text the engine still validates.
 */
export function AnswerAffordances({
  question,
  disabled,
  pending,
  onAnswer,
}: {
  question: CurrentQuestion;
  disabled: boolean;
  /** Whatever is currently typed in the composer below. A multi_select answer can be
   *  options AND something the list did not anticipate, so Confirm sends both rather
   *  than making the respondent choose which half of their answer to keep. */
  pending: string;
  onAnswer: (text: string) => void;
}) {
  const msg = useT();
  const [picked, setPicked] = useState<string[]>([]);
  const [typed, setTyped] = useState("");

  if (question.answer_type === "yes_no") {
    return (
      <div className="afford">
        {/* Translating these is correct rather than risky: the chip's text is sent as
            the respondent's message, the model interprets it, and what reaches the
            database is the boolean its tool call returns. "Sí" records true. */}
        {[msg.run.yes, msg.run.no].map((option) => (
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
          <span className="chip chip-dashed afford-hint">{msg.run.orSayIt}</span>
        ) : null}
      </div>
    );
  }

  if (question.answer_type === "multi_select") {
    const toggle = (option: string) =>
      setPicked((current) =>
        current.includes(option) ? current.filter((o) => o !== option) : [...current, option],
      );
    // Chips and composer are one answer, not two competing ones. Confirm used to send
    // only the chips and Send only the text, so a respondent who ticked two options and
    // typed a third thing lost whichever half they did not submit with. The engine has
    // always been able to store both: validate_answer sorts each value into the option
    // list or the write-ins, and a multi_select value carries `options` and `other`
    // together.
    const writeIn = question.allow_other ? pending.trim() : "";
    const parts = [...picked, ...(writeIn ? [writeIn] : [])];
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
          disabled={disabled || parts.length === 0}
          onClick={() => onAnswer(parts.join(", "))}
        >
          {msg.run.confirm} {parts.length ? `(${parts.length})` : ""}
        </button>
        {writeIn ? (
          // Said out loud, because the count silently going up by one is not enough to
          // tell someone their typed words are about to be sent with their ticks.
          <span className="afford-hint">{msg.run.andWhatYouTyped}</span>
        ) : null}
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
