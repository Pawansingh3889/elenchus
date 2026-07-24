"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useCurrentUser, usePublishedSurveys, useStartRun } from "@/lib/queries";
import { useUserStore } from "@/lib/store";

export default function RespondPage() {
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: surveys, isLoading, error } = usePublishedSurveys();
  const start = useStartRun();
  const router = useRouter();

  // Taking a survey is respondent-only (the backend refuses authors); send authors
  // back to Build rather than let them start a run under their own name.
  const isAuthor = currentUser?.role === "author";
  useEffect(() => {
    if (isAuthor) router.replace("/");
  }, [isAuthor, router]);

  if (!currentUserId) {
    return <div className="empty">Pick a user in the top bar to take a survey.</div>;
  }
  if (isAuthor) {
    return <div className="empty">Taking you to Build…</div>;
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>Open surveys</h1>
      </div>

      {isLoading ? <div className="muted">Loading…</div> : null}
      {error ? <div className="error-text">{(error as Error).message}</div> : null}
      {start.error ? <div className="error-text">{(start.error as Error).message}</div> : null}

      <div className="survey-list">
        {surveys?.map((survey) => (
          <div key={survey.id} className="survey-row">
            <div>
              <div className="template-title">{survey.title}</div>
              <div className="template-meta">
                {survey.question_count} question{survey.question_count === 1 ? "" : "s"}
              </div>
            </div>
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
          </div>
        ))}
        {surveys && surveys.length === 0 ? (
          <div className="muted">Nothing published yet. Publish a template to open it here.</div>
        ) : null}
      </div>
    </div>
  );
}
