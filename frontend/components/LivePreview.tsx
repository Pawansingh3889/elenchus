"use client";

import { useState } from "react";

import type { QuestionInput } from "@/lib/types";

function Affordance({ q }: { q: QuestionInput }) {
  if (q.answer_type === "single_select" || q.answer_type === "multi_select") {
    return (
      <div className="chat-afford">
        {q.options.map((o, i) => (
          <span className="chip" key={i}>
            {o || "…"}
          </span>
        ))}
        {q.allow_other ? <span className="chip chip-dashed">other…</span> : null}
      </div>
    );
  }
  if (q.answer_type === "yes_no") {
    return (
      <div className="chat-afford">
        <span className="chip">Yes</span>
        <span className="chip">No</span>
      </div>
    );
  }
  if (q.answer_type === "rating") {
    return <div className="stars">★★★★★</div>;
  }
  return null;
}

interface Props {
  questions: QuestionInput[];
}

export function LivePreview({ questions }: Props) {
  const [mode, setMode] = useState<"chat" | "form">("chat");

  return (
    <aside className="preview">
      <div className="preview-head">
        <span className="card-label">Live preview</span>
        <div className="segmented">
          <button className={mode === "chat" ? "active" : ""} onClick={() => setMode("chat")}>
            Conversational
          </button>
          <button className={mode === "form" ? "active" : ""} onClick={() => setMode("form")}>
            Form
          </button>
        </div>
      </div>
      <div className="preview-body">
        {questions.length === 0 ? (
          <div className="preview-empty">Add a question to see the preview.</div>
        ) : null}
        {questions.map((q, i) =>
          mode === "chat" ? (
            <div key={i}>
              <div className="chat-q">{q.text || "Untitled question"}</div>
              <Affordance q={q} />
            </div>
          ) : (
            <div className="form-q" key={i}>
              <label>
                {i + 1}. {q.text || "Untitled question"}
                {q.required ? " *" : ""}
              </label>
              <span className="type-hint">{q.answer_type}</span>
              <Affordance q={q} />
            </div>
          ),
        )}
      </div>
    </aside>
  );
}
