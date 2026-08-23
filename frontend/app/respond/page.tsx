"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  useCurrentUser,
  useMyUnfinishedRuns,
  usePublishedSurveys,
  useStartRun,
  useStartRunPublic,
} from "@/lib/queries";
import { useT } from "@/lib/i18n/useT";
import { useUserStore } from "@/lib/store";

export default function RespondPage() {
  const { common, respond } = useT();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: surveys, isLoading, error } = usePublishedSurveys();
  const start = useStartRun();
  const startPublic = useStartRunPublic();
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

  // If there's a public survey link, auto-start a run
  useEffect(() => {
    if (publicSurveyId && !isPublicMode) {
      // Use a small timeout to avoid synchronous state update in effect
      setTimeout(() => setIsPublicMode(true), 0);
      startPublic.mutate(publicSurveyId, {
        onSuccess: (run) => router.push(`/runs/${run.id}`),
        onError: (error) => {
          console.error("Failed to start public survey:", error);
          setIsPublicMode(false);
        },
      });
    }
  }, [publicSurveyId, isPublicMode, startPublic, router]);

  // Taking a survey is respondent-only (the backend refuses authors); send authors
  // back to Build rather than let them start a run under their own name.
  const isAuthor = currentUser?.may_author === true;
  useEffect(() => {
    if (isAuthor && !isPublicMode) router.replace("/");
  }, [isAuthor, router, isPublicMode]);

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
