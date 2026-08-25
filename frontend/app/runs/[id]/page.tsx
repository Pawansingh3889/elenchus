"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { AnswerAffordances } from "@/components/AnswerAffordances";
import { AutoGrowTextarea } from "@/components/AutoGrowTextarea";
import { Transcript } from "@/components/Transcript";
import { useT } from "@/lib/i18n/useT";
import { useDeleteRun, useRewindRun, useRun, useSendRunMessage } from "@/lib/queries";
import { useUserStore } from "@/lib/store";
import type { AnswerType } from "@/lib/types";

export default function RunPage() {
  const { common, run: text } = useT();
  const { id } = useParams<{ id: string }>();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const { data: run, isLoading, error } = useRun(id);
  const send = useSendRunMessage(id);
  const rewind = useRewindRun(id);
  const remove = useDeleteRun(id);
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // A structured question with its own typed control (chips, stars, a number/date
  // field) answers through that control alone. The free-text composer underneath it is
  // then a second input with a second Send, and the route a numeric answer could sneak
  // in as prose and bypass the data type. Hide it for those types; probes are open prose
  // so they keep it. multi_select uses its own Confirm button that bundles chips + write-in.
  const SELF_CONTAINED: AnswerType[] = ["yes_no", "single_select", "rating", "number", "date", "multi_select"];
  const composerHidden =
    isLoading ||
    (!!run?.current_question &&
      !run.awaiting_follow_up &&
      SELF_CONTAINED.includes(run.current_question.answer_type));

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [run?.messages.length, send.isPending]);

  if (!currentUserId) {
    return <div className="empty">{text.pickUser}</div>;
  }
  // Not gated on may_author: an author can be the named audience of their own
  // "person" survey, and the backend's own may_answer check (asked when the run
  // was started, and again on every message) is the one place this question gets
  // answered. See frontend/app/respond/page.tsx for the fuller note.
  if (isLoading) return <div className="muted">{common.loading}</div>;
  if (error) return <div className="error-text">{(error as Error).message}</div>;
  if (!run) return null;

  // One request at a time. A rewind fired while a turn is in flight would race the answer
  // that turn is still writing, and the engine's row lock would refuse it anyway.
  const busy = send.isPending || rewind.isPending || remove.isPending;

  const answer = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    // Cleared once the turn is recorded, not before. The engine appends the respondent's
    // message and only flushes it, so a turn that fails rolls it back: clearing up front
    // left the text in neither the transcript nor the box, and a long answer had to be
    // written again from memory on top of being told to try again.
    send.mutate(trimmed, { onSuccess: () => setDraft("") });
  };

  // Destructive and irreversible: it discards the answer, anything the engine probed
  // from it, and that stretch of the conversation. The builder confirms before losing an
  // author's typed options for the same reason.
  const editPrevious = () => {
    if (busy || !window.confirm(text.editPreviousConfirm)) return;
    setDraft("");
    rewind.mutate();
  };

  // Withdraw everything, which is a different thing from taking back one answer and is
  // deliberately offered on a finished run as well as an unfinished one: a completed run
  // is the only kind worth withdrawing, and the author having read it is the reason
  // someone asks rather than a reason to refuse. Leaves for the survey list on success,
  // because staying would leave the respondent looking at a run that no longer exists.
  const withdraw = () => {
    if (busy || !window.confirm(text.withdrawConfirm)) return;
    remove.mutate(undefined, { onSuccess: () => router.push("/respond") });
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
          {/* inlineSize, not width: every other bar in the app uses the logical
              property, and this one filled from the left in Arabic and Hebrew while the
              rest of the page read right to left. */}
          <span style={{ inlineSize: `${progress}%` }} />
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
      {remove.error ? <div className="error-text">{(remove.error as Error).message}</div> : null}

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
              pending={draft}
              onAnswer={answer}
            />
          ) : null}
          {!composerHidden && (
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
          )}

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

      {/* Outside the done/not-done split on purpose, and the only control that is. Every
          other affordance here belongs to answering, which a finished run has stopped
          doing; withdrawing is not part of answering and a finished run is the main case
          for it. */}
      <div className="chat-withdraw">
        <button className="link-btn link-btn-danger" onClick={withdraw} disabled={busy}>
          {text.withdraw}
        </button>
        <span className="muted">{text.withdrawHint}</span>
      </div>
    </div>
  );
}
