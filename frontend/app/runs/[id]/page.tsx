"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { AnswerAffordances } from "@/components/AnswerAffordances";
import { AutoGrowTextarea } from "@/components/AutoGrowTextarea";
import { Transcript } from "@/components/Transcript";
import { useT } from "@/lib/i18n/useT";
import { useCurrentUser, useRewindRun, useRun, useSendRunMessage } from "@/lib/queries";
import { useUserStore } from "@/lib/store";

export default function RunPage() {
  const { common, run: text, respond } = useT();
  const { id } = useParams<{ id: string }>();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: run, isLoading, error } = useRun(id);
  const send = useSendRunMessage(id);
  const rewind = useRewindRun(id);
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
    return <div className="empty">{text.pickUser}</div>;
  }
  if (isAuthor) {
    return <div className="empty">{respond.goingToBuild}</div>;
  }
  if (isLoading) return <div className="muted">{common.loading}</div>;
  if (error) return <div className="error-text">{(error as Error).message}</div>;
  if (!run) return null;

  // One request at a time. A rewind fired while a turn is in flight would race the answer
  // that turn is still writing, and the engine's row lock would refuse it anyway.
  const busy = send.isPending || rewind.isPending;

  const answer = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setDraft("");
    send.mutate(trimmed);
  };

  // Destructive and irreversible: it discards the answer, anything the engine probed
  // from it, and that stretch of the conversation. The builder confirms before losing an
  // author's typed options for the same reason.
  const editPrevious = () => {
    if (busy || !window.confirm(text.editPreviousConfirm)) return;
    setDraft("");
    rewind.mutate();
  };

  const done = run.status !== "in_progress";
  const progress = run.total ? Math.round((run.answered / run.total) * 100) : 0;
  // There has to be an answer to take back. `answered` counts scripted answers, which is
  // exactly what the engine rewinds: a follow-up is never the last thing recorded on its
  // own, so it cannot be the thing that comes back.
  const canEditPrevious = !done && run.answered > 0;

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
        {busy ? (
          <div className="bubble bubble-assistant typing">
            <span />
            <span />
            <span />
          </div>
        ) : null}
        <div ref={endRef} />
      </Transcript>

      {send.error ? <div className="error-text">{(send.error as Error).message}</div> : null}
      {rewind.error ? <div className="error-text">{(rewind.error as Error).message}</div> : null}

      {done ? (
        <div className="chat-done">{text.done}</div>
      ) : (
        <>
          {/* Not while the engine is probing. `current_question` still describes the
              scripted question, so its typed controls would answer the wrong question:
              [Yes] [No] chips under "could you describe the issues you've encountered?",
              and the description recorded as "Yes". A probe is always open prose, so the
              composer below is the whole affordance it needs. */}
          {run.current_question && !run.awaiting_follow_up ? (
            <AnswerAffordances
              key={run.current_question.id}
              question={run.current_question}
              disabled={busy}
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
            <AutoGrowTextarea
              value={draft}
              placeholder={text.answerPlaceholder}
              disabled={busy}
              onChange={setDraft}
              // A textarea does not submit its form on Enter the way an input does, and a
              // respondent mid-conversation expects it to. Shift+Enter still opens a line,
              // which is the whole point of the box wrapping now.
              onEnter={() => answer(draft)}
            />
            <button className="btn btn-primary" type="submit" disabled={busy || !draft.trim()}>
              {text.send}
            </button>
          </form>

          {/* Offered next to the composer rather than on the bubble itself: what comes
              back is the last *answer*, which may span several bubbles once the engine has
              probed it, so pinning the control to one of them would misdescribe it. */}
          {canEditPrevious ? (
            <div className="chat-amend">
              <button className="link-btn" onClick={editPrevious} disabled={busy}>
                {text.editPrevious}
              </button>
              <span className="muted">{text.editPreviousHint}</span>
            </div>
          ) : null}

          {/* Nothing to save: every turn is already persisted server-side, so leaving
              is safe and the run is offered back on the home page. Saying so is the
              honest version of a "save and exit" button. */}
          <div className="chat-later">
            <button className="link-btn" onClick={() => router.push("/respond")}>
              {text.finishLater}
            </button>
            <span className="muted">{text.finishLaterHint}</span>
          </div>
        </>
      )}
    </div>
  );
}
