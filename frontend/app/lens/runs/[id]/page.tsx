"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Tile } from "@/components/lens/LensStripView";
import { SpanTree } from "@/components/lens/SpanTree";
import { dollars, milliseconds, tokenCount } from "@/lib/lensFormat";
import { useLensRuns, useLensSpans, useMe } from "@/lib/queries";

/** One run's trace: its totals on top, then every turn as a waterfall of spans. */
export default function LensRun() {
  const { id } = useParams<{ id: string }>();
  const { data: me, isLoading: meLoading } = useMe();
  const admin = me?.is_admin === true;
  const spans = useLensSpans(id, admin);
  const runs = useLensRuns(admin);
  const run = runs.data?.find((candidate) => candidate.run_id === id);

  if (meLoading) return <p className="empty">Loading…</p>;
  if (!admin) return <p className="empty">Sign in as an administrator to use the lens.</p>;

  return (
    <div className="page lens">
      <div className="page-head">
        <h1>{run?.survey_title ?? "Run trace"}</h1>
        <Link href="/lens" className="btn btn-secondary">
          All runs
        </Link>
      </div>
      <p className="lens-provenance">
        Measured from the trace. The lighter part of an attempt&rsquo;s bar is the time before
        its first token; the rest is the model writing.
      </p>

      <ErrorBanner error={spans.error ?? runs.error} />

      {run ? (
        <div className="lens-tiles">
          <Tile label="Turns" value={String(run.turns)} />
          <Tile label="Asks of the model" value={`${run.decisions} (${run.retries} retries)`} />
          <Tile label="Attempts" value={`${run.attempts} (${run.failed_attempts} failed)`} />
          <Tile
            label="Tokens in"
            value={`${tokenCount(run.prompt_tokens, run.unmetered_attempts)} (${tokenCount(run.cached_tokens, run.unmetered_attempts)} cached)`}
          />
          <Tile label="Tokens out" value={tokenCount(run.completion_tokens, run.unmetered_attempts)} />
          <Tile label="Cost" value={dollars(run.cost_usd, run.unmetered_attempts)} />
          <Tile label="Respondent waited" value={milliseconds(run.turn_ms)} />
          <Tile label="First token p50" value={milliseconds(run.first_token_ms_p50)} />
        </div>
      ) : null}

      {spans.data ? <SpanTree spans={spans.data} /> : null}
    </div>
  );
}
