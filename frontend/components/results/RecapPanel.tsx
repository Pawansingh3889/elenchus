"use client";

import { Sparkles } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import { Card, CardLabel } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useT } from "@/lib/i18n/useT";
import { useSummariseSurvey, useSurveyRecap } from "@/lib/queries";
import type { SurveySummary } from "@/lib/types";

/**
 * What the whole survey found, in the model's words and the database's numbers.
 *
 * Two things this panel has to get right, and both were wrong before.
 *
 * **A recap survives a navigation.** It used to render out of the mutation's own
 * result, so leaving the tab and coming back lost it and the author spent another model
 * call reading prose the column already held. It reads from a GET now, and the
 * generate mutation seeds that same cache key.
 *
 * **A refusal reads as a refusal.** When the checker will not stand behind the headline
 * the API answers 409 with its reasons in the message. That used to render in the same
 * red line as an outage, so the author was invited to retry something that would fail
 * identically, and the reasons, which are the only useful part, looked like noise.
 * ErrorBanner splits the two and withholds the retry on a refusal.
 *
 * Every figure here is read out of the report, never out of the model: a finding is
 * prose with no digits in it, which the API enforces, and the tally beside it is the
 * question's own. So the words can be arguable and the numbers cannot be wrong.
 */
function RecapBody({ recap }: { recap: SurveySummary }) {
  const msg = useT();
  return (
    <>
      <h3 className="text-xl font-bold leading-tight text-ink md:text-2xl">
        {recap.headline}
      </h3>

      <ul className="flex flex-col gap-2">
        {recap.findings.map((finding, i) => (
          <li key={i} className="flex flex-col">
            <span className="text-ink">{finding.statement}</span>
            <span className="text-sm text-muted">
              {finding.question_text
                ? msg.report.fromQuestion(
                    (finding.question_position ?? 0) + 1,
                    finding.question_text,
                  )
                : null}
              {finding.counts.length > 0 ? (
                <>
                  {" "}
                  {finding.counts
                    .filter((c) => c.count > 0)
                    .map((c) => `${c.label} ${c.count}`)
                    .join(" · ")}
                  {finding.average !== null
                    ? ` · ${msg.report.average(finding.average.toFixed(1))}`
                    : ""}
                </>
              ) : null}
            </span>
          </li>
        ))}
      </ul>

      {/* The evidence line. Computed on the server from the report, so the one line
          that qualifies the findings above is never the model's to get wrong. */}
      <p className="text-sm text-muted">{recap.caveat}</p>

      {/* Which prompt and which tier wrote it. A recap that reads worse than it used to
          may be a prompt change or a model change, and this is what tells them apart. */}
      {recap.prompt_version && recap.model ? (
        <p className="text-xs text-muted">
          {msg.report.recapWrittenBy(recap.prompt_version, recap.model)}
        </p>
      ) : null}
    </>
  );
}

export function RecapPanel({
  templateId,
  runsCompleted,
  hidden,
}: {
  templateId: string;
  runsCompleted: number;
  /** A slice is showing, so the recap would be describing a different set of people
   *  from the numbers beside it. */
  hidden?: boolean;
}) {
  const msg = useT();
  const stored = useSurveyRecap(templateId);
  const write = useSummariseSurvey(templateId);

  // Nothing to summarise, and the API refuses it, so the button is not offered.
  if (runsCompleted === 0) return null;

  if (hidden) {
    return (
      <p className="text-sm text-muted">{msg.report.recapHiddenWhileSliced}</p>
    );
  }

  const recap = stored.data?.recap ?? null;
  const outdated = stored.data?.absence === "outdated";

  const action = (
    <Button
      variant="ai"
      onClick={() => write.mutate(Boolean(recap) || outdated)}
      disabled={write.isPending}
    >
      <Sparkles aria-hidden />
      {write.isPending
        ? msg.report.recapWorking
        : recap || outdated
          ? msg.report.recapAgain
          : msg.report.recapAsk}
    </Button>
  );

  if (stored.isLoading) return <Skeleton className="h-32 w-full" />;

  // No recap to show, and the two reasons read differently. `outdated` means one was
  // written and the responses have moved past it; the API withholds it rather than
  // serving it, on the rule that a recap of eight responses read after twenty have
  // arrived is not stale but wrong, and nothing in the prose would say so.
  if (!recap) {
    return (
      <div className="flex flex-col gap-2">
        <EmptyState
          title={outdated ? msg.report.recapStale : msg.report.recapAsk}
          body={outdated ? msg.report.recapOutdatedBody : msg.report.recapNever}
          action={action}
        />
        {write.error ? <ErrorBanner error={write.error} /> : null}
      </div>
    );
  }

  return (
    <Card className="flex flex-col gap-3 border-ai-border bg-ai-fill p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <CardLabel>{msg.report.recapFrom(recap.runs_included)}</CardLabel>
        {action}
      </div>

      <RecapBody recap={recap} />

      {write.error ? <ErrorBanner error={write.error} /> : null}
    </Card>
  );
}
