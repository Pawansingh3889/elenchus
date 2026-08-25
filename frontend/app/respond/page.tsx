"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useMyUnfinishedRuns, usePublishedSurveys, useStartRun } from "@/lib/queries";
import { useT } from "@/lib/i18n/useT";
import { useUserStore } from "@/lib/store";

export default function RespondPage() {
  const { common, respond } = useT();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const { data: surveys, isLoading, error } = usePublishedSurveys();
  const start = useStartRun();
  const { data: unfinished } = useMyUnfinishedRuns();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPublicMode, setIsPublicMode] = useState(false);
  
  // Check for public survey link (e.g., /respond?survey=<template_id>)
  const publicSurveyId = searchParams.get("survey");
  const publicRunId = searchParams.get("run");

  // If there's a public run link, navigate directly to it
  useEffect(() => {
    if (publicRunId) {
      router.push(`/runs/${publicRunId}`);
    }
  }, [publicRunId, router]);

  // If there's a public survey link, auto-start a run under whoever get_current_user
  // actually resolves: the signed-in respondent if there is one, the server's own
  // anonymous-caller default otherwise. This used to go through a dedicated "public"
  // endpoint that hardcoded a seeded author as the respondent regardless of who was
  // signed in, so a real respondent opening a survey card here started a run
  // attributed to that seeded author instead of themselves, and their own browser
  // then refused to let them into a run that was not theirs.
  useEffect(() => {
    if (publicSurveyId && !isPublicMode) {
      // Use a small timeout to avoid synchronous state update in effect
      setTimeout(() => setIsPublicMode(true), 0);
      start.mutate(publicSurveyId, {
        onSuccess: (run) => router.push(`/runs/${run.id}`),
        onError: (error) => {
          console.error("Failed to start survey:", error);
          setIsPublicMode(false);
        },
      });
    }
  }, [publicSurveyId, isPublicMode, start, router]);

  // In public mode, show loading state
  if (isPublicMode) {
    return (
      <div className="page">
        <div className="page-head">
          <h1>{respond.title}</h1>
        </div>
        <div className="muted">{respond.loading}</div>
      </div>
    );
  }

  if (!currentUserId) {
    return <div className="empty">{respond.pickUser}</div>;
  }

  // Not gated on may_author: an author can be the named audience of their own
  // "person" survey (the attributable-answer warning in the composer exists for
  // exactly this case), and usePublishedSurveys already filters through may_answer
  // server-side. Blocking every author here regardless was a second, coarser copy
  // of that same question, which backend/app/conduct/router.py's own docstring
  // says deliberately not to keep: an author with nothing to answer just sees the
  // empty state below, same as anyone else.
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
