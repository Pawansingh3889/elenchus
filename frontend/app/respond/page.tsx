"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import {
  useCurrentUser,
  useMyUnfinishedRuns,
  usePublishedSurveys,
  useStartRun,
} from "@/lib/queries";
import { useT } from "@/lib/i18n/useT";
import { useUserStore } from "@/lib/store";

export default function RespondPage() {
  const { common, respond } = useT();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: surveys, isLoading, error } = usePublishedSurveys();
  const start = useStartRun();
  const { data: unfinished } = useMyUnfinishedRuns();
  const router = useRouter();

  // Taking a survey is respondent-only (the backend refuses authors); send authors
  // back to Build rather than let them start a run under their own name.
  const isAuthor = currentUser?.role === "author";
  useEffect(() => {
    if (isAuthor) router.replace("/");
  }, [isAuthor, router]);

  if (!currentUserId) {
    return <div className="empty">{respond.pickUser}</div>;
  }
  if (isAuthor) {
    return <div className="empty">{respond.goingToBuild}</div>;
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>{respond.title}</h1>
      </div>

      {isLoading ? <div className="muted">{common.loading}</div> : null}
      {error ? <div className="error-text">{(error as Error).message}</div> : null}
      {start.error ? <div className="error-text">{(start.error as Error).message}</div> : null}

      <div className="survey-list">
        {surveys?.map((survey) => {
          // An unfinished run on this survey turns Start into Continue. Starting again
          // would open a second run and strand the first half-answered.
          const open = unfinished?.find((r) => r.template_id === survey.id);
          return (
            <div key={survey.id} className="survey-row">
              <div>
                <div className="template-title">{survey.title}</div>
                <div className="template-meta">
                  {survey.question_count} question{survey.question_count === 1 ? "" : "s"}
                  {survey.estimated_minutes
                    ? ` · about ${survey.estimated_minutes} min${
                        survey.estimated_minutes === 1 ? "" : "s"
                      }`
                    : ""}
                  {open ? ` · ${open.answered} of ${open.total} answered` : ""}
                </div>
              </div>
              {survey.answered ? (
                // Already finished. The row stays rather than vanishing, because a survey
                // that disappears reads as a bug, and Start here would now be a button
                // that can only fail: one answer per person is enforced in the engine.
                <span className="pill pill-closed">{respond.answered}</span>
              ) : open ? (
                <button
                  className="btn btn-primary"
                  onClick={() => router.push(`/runs/${open.id}`)}
                >
                  Continue
                </button>
              ) : (
                <button
                  className="btn btn-primary"
                  disabled={start.isPending}
                  onClick={() =>
                    start.mutate(survey.id, {
                      onSuccess: (run) => router.push(`/runs/${run.id}`),
                    })
                  }
                >
                  {start.isPending ? "Starting…" : "Start"}
                </button>
              )}
            </div>
          );
        })}
        {surveys && surveys.length === 0 ? (
          <div className="muted">{respond.empty}</div>
        ) : null}
      </div>
    </div>
  );
}
