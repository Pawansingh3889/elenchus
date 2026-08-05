"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { AnswerAffordances } from "@/components/AnswerAffordances";
import { Transcript } from "@/components/Transcript";
import { useCurrentUser, useRun, useSendRunMessage } from "@/lib/queries";
import { useUserStore } from "@/lib/store";

export default function RunPage() {
  const { id } = useParams<{ id: string }>();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: run, isLoading, error } = useRun(id);
  const send = useSendRunMessage(id);
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [run?.messages.length, send.isPending]);

  // Conducting is respondent-only; an author following a run link is sent to Build.
  const isAuthor = currentUser?.role === "author";
  useEffect(() => {
    if (isAuthor) router.replace("/");
  }, [isAuthor, router]);

  if (!currentUserId) {
    return <div className="empty">Pick a user in the top bar to continue this survey.</div>;
  }
  if (isAuthor) {
    return <div className="empty">Taking you to Build…</div>;
  }
  if (isLoading) return <div className="muted">Loading…</div>;
  if (error) return <div className="error-text">{(error as Error).message}</div>;
  if (!run) return null;

  const answer = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || send.isPending) return;
    setDraft("");
    send.mutate(trimmed);
  };

  const done = run.status !== "in_progress";
  const progress = run.total ? Math.round((run.answered / run.total) * 100) : 0;

  return (
    <div className="chat">
      <div className="chat-head">
        <div className="chat-progress">
          {run.answered} of {run.total} answered
        </div>
        <div className="progress-bar">
          <span style={{ width: `${progress}%` }} />
        </div>
      </div>

      <Transcript messages={run.messages}>
        {send.isPending ? (
          <div className="bubble bubble-assistant typing">
            <span />
            <span />
            <span />
          </div>
        ) : null}
        <div ref={endRef} />
      </Transcript>

      {send.error ? <div className="error-text">{(send.error as Error).message}</div> : null}

      {done ? (
        <div className="chat-done">Thanks. Your answers are saved.</div>
      ) : (
        <>
          {run.current_question ? (
            <AnswerAffordances
              key={run.current_question.id}
              question={run.current_question}
              disabled={send.isPending}
              onAnswer={answer}
            />
          ) : null}
          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault();
              answer(draft);
            }}
          >
            <input
              className="field"
              value={draft}
              placeholder="Type your answer…"
              disabled={send.isPending}
              onChange={(e) => setDraft(e.target.value)}
            />
            <button
              className="btn btn-primary"
              type="submit"
              disabled={send.isPending || !draft.trim()}
            >
              Send
            </button>
          </form>
          {/* Nothing to save: every turn is already persisted server-side, so leaving
              is safe and the run is offered back on the home page. Saying so is the
              honest version of a "save and exit" button. */}
          <div className="chat-later">
            <button className="link-btn" onClick={() => router.push("/respond")}>
              Finish later
            </button>
            <span className="muted"> — your answers so far are saved; pick up where you left off.</span>
          </div>
        </>
      )}
    </div>
  );
}
