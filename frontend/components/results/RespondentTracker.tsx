"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatRelativeTime } from "@/lib/utils";
import { useT } from "@/lib/i18n/useT";
import { useRespondents, useRespondentStreamConnection } from "@/lib/queries";
import type { RespondentRow } from "@/lib/types";

interface RespondentTrackerProps {
  templateId: string;
}

/**
 * Real-time respondent tracking panel for the dashboard/results page.
 * Shows who is currently active on the survey with live updates via SSE.
 */
export function RespondentTracker({ templateId }: RespondentTrackerProps) {
  const msg = useT();
  const [respondents, setRespondents] = useState<RespondentRow[]>([]);
  const { data: initialRespondents, isLoading, error } = useRespondents(templateId);

  // Initialize with server data
  useEffect(() => {
    if (initialRespondents) {
      // Use a small timeout to avoid synchronous state update in effect
      setTimeout(() => setRespondents(initialRespondents), 0);
    }
  }, [initialRespondents]);

  // Connect to SSE stream for real-time updates
  useRespondentStreamConnection(templateId, (updated) => {
    setRespondents(updated);
  });

  // Separate respondents by status
  const active = respondents.filter(
    (r) => r.current_status === "in_progress" && r.current_run_id
  );
  const completed = respondents.filter((r) => r.completed_runs > 0);
  const neverStarted = respondents.filter(
    (r) => r.total_runs === 0 || (r.in_progress_runs === 0 && r.completed_runs === 0)
  );

  if (isLoading) {
    return (
      <Card className="p-4">
        <div className="flex flex-col gap-3">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-40 w-full" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-4">
        <p className="text-sm text-err-text">{msg.common.notFound}</p>
      </Card>
    );
  }

  return (
    <Card className="flex flex-col p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h2 className="text-md font-semibold">{msg.results.respondents}</h2>
        <div className="flex items-center gap-2">
          <Badge variant="accent">{respondents.length} total</Badge>
          <Badge variant="warn">{active.length} active</Badge>
          <Badge variant="accent">{completed.length} completed</Badge>
        </div>
      </div>

      {/* Active respondents - real-time */}
      {active.length > 0 && (
        <section className="mb-4">
          <h3 className="text-sm font-medium text-warn-text mb-2 flex items-center gap-2">
            <span className="size-2 rounded-full bg-warn-text animate-pulse" aria-hidden />
            Live Sessions
          </h3>
          <div className="space-y-2">
            {active.map((r) => (
              <div
                key={r.respondent_id}
                className="flex items-center justify-between gap-3 p-3 rounded-lg bg-ai-fill/30 border border-ai-border"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-strong text-xs font-semibold text-on-slab shrink-0">
                    {r.respondent_label.replace("Respondent ", "R")}
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-ink truncate">{r.display_name}</p>
                    <p className="text-xs text-muted">
                      {r.respondent_label} · {msg.home.inProgress}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted">
                  {r.last_activity_at && (
                    <span className="flex items-center gap-1">
                      <span className="size-1.5 rounded-full bg-accent-strong animate-pulse" aria-hidden />
                      Active {formatRelativeTime(r.last_activity_at)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Completed respondents */}
      {completed.length > 0 && (
        <section className="mb-4">
          <h3 className="text-sm font-medium text-muted mb-2">Completed</h3>
          <div className="space-y-1">
            {completed.map((r) => (
              <div
                key={r.respondent_id}
                className="flex items-center justify-between gap-2 p-2 rounded border border-line"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-accent text-xs font-semibold text-on-slab shrink-0">
                    {r.respondent_label.replace("Respondent ", "R")}
                  </div>
                  <p className="text-sm font-medium text-ink truncate">{r.display_name}</p>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted">
                  <span>{r.completed_runs} of {r.total_runs} completed</span>
                  {r.last_completed_at && (
                    <span>Finished {formatRelativeTime(r.last_completed_at)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Never started */}
      {neverStarted.length > 0 && (
        <section>
          <h3 className="text-sm font-medium text-muted mb-2">Not Started</h3>
          <div className="space-y-1">
            {neverStarted.map((r) => (
              <div
                key={r.respondent_id}
                className="flex items-center gap-2 p-2 rounded border border-line opacity-50"
              >
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-muted-light text-xs font-medium text-muted shrink-0">
                  {r.respondent_label.replace("Respondent ", "R")}
                </div>
                <p className="text-sm text-muted truncate">{r.display_name}</p>
                <span className="text-xs text-muted ml-auto">Has not opened</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {respondents.length === 0 && (
        <p className="text-center text-muted py-8">{msg.results.nothingAnswered}</p>
      )}
    </Card>
  );
}