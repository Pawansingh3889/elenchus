"use client";

import { type ReactNode, useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { probability } from "@/lib/interpFormat";
import { dollars, milliseconds, moment } from "@/lib/lensFormat";
import { useLensScope, useSelectedAsk } from "@/lib/lensScope";
import { useAnalyse, useAttribute, useInterpAsks, useInterpStatus } from "@/lib/queries";
import type { CapturedAsk, InterpStatus, StoredAnalysis } from "@/lib/schemas";

type Action = "read" | "attribute";

/**
 * The captured calls in scope, and the only controls that spend the local model's time.
 *
 * Reading and attributing are separate buttons because they cost very different amounts:
 * on a laptop CPU a reading takes about a minute and a half and an attribution about five.
 * One runs at a time, its seconds count up where its button was, and both are stored, so
 * nothing here ever reads the same call twice.
 */
export function InterpAsks({ admin, need }: { admin: boolean; need: "reading" | "attribution" }) {
  const [scope] = useLensScope();
  const [selected, select] = useSelectedAsk();
  const status = useInterpStatus(admin);
  const asks = useInterpAsks(scope, admin);
  const analyse = useAnalyse();
  const attribute = useAttribute();
  const running: { spanId: string; action: Action; since: number } | null = analyse.isPending
    ? { spanId: analyse.variables, action: "read", since: analyse.submittedAt }
    : attribute.isPending
      ? { spanId: attribute.variables, action: "attribute", since: attribute.submittedAt }
      : null;
  const now = useClock(running !== null);
  const ready = status.data?.reachable === true;
  const rows = asks.data ?? [];

  const start = (ask: CapturedAsk, action: Action) => {
    select(ask.span_id);
    if (action === "read") analyse.mutate(ask.span_id);
    else attribute.mutate(ask.span_id);
  };

  return (
    <section className="lens-section">
      <h2 className="lens-heading">Captured calls</h2>
      <StatusNote status={status.data} />
      <ErrorBanner error={asks.error ?? analyse.error ?? attribute.error} />
      {rows.length === 0 && !asks.isLoading ? (
        <p className="lens-note">
          No captured calls in this scope. Prompts are kept for calls made from 13 Sep 2026 on,
          so answer a survey to make one.
        </p>
      ) : (
        <div className="lens-table-wrap">
          <table className="lens-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Survey</th>
                <th>Hosted pick</th>
                <th>Check</th>
                <th className="num">Hosted call</th>
                <th>Qwen&rsquo;s pick</th>
                <th className="num">Qwen on the hosted pick</th>
                <th className="num">Reading</th>
                {need === "attribution" ? <th className="num">Attribution</th> : null}
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((ask) => (
                <tr key={ask.span_id} aria-selected={ask.span_id === selected}>
                  <td>{moment(ask.started_at)}</td>
                  <td>{ask.survey_title}</td>
                  <td>{ask.hosted_pick ?? "no checked call"}</td>
                  <td className={ask.outcome === "refused" ? "lens-refused" : undefined}>
                    {ask.outcome ?? ""}
                  </td>
                  <td className="num">
                    {milliseconds(ask.hosted_ms)} · {dollars(ask.hosted_cost_usd)}
                  </td>
                  <td>
                    {ask.qwen_pick ?? ""}
                    {ask.agrees === false ? " (differs)" : ""}
                  </td>
                  <td className="num">
                    {ask.analysed ? probability(ask.qwen_probability_of_hosted_pick) : ""}
                  </td>
                  <td className="num">
                    {ask.analysed
                      ? `${milliseconds(ask.analysis_ms)} · ${dollars(ask.analysis_cost_usd)}`
                      : ""}
                  </td>
                  {need === "attribution" ? (
                    <td className="num">
                      {ask.attributed
                        ? `${milliseconds(ask.attribution_ms)} · ${dollars(ask.attribution_cost_usd)}`
                        : ""}
                    </td>
                  ) : null}
                  <td>
                    <ActionCell
                      ask={ask}
                      need={need}
                      selected={ask.span_id === selected}
                      running={running}
                      elapsed={running ? Math.max(0, Math.round((now - running.since) / 1000)) : 0}
                      ready={ready}
                      onStart={start}
                      onShow={() => select(ask.span_id)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function ActionCell({
  ask,
  need,
  selected,
  running,
  elapsed,
  ready,
  onStart,
  onShow,
}: {
  ask: CapturedAsk;
  need: "reading" | "attribution";
  selected: boolean;
  running: { spanId: string; action: Action } | null;
  elapsed: number;
  ready: boolean;
  onStart: (ask: CapturedAsk, action: Action) => void;
  onShow: () => void;
}) {
  if (running?.spanId === ask.span_id) {
    return (
      <span className="lens-running">
        {running.action === "read" ? "Reading" : "Attributing"}, {elapsed} s
      </span>
    );
  }
  const busy = running !== null;
  if (!ask.analysed) {
    return (
      <button
        type="button"
        className="btn btn-secondary"
        disabled={busy || !ready}
        onClick={() => onStart(ask, "read")}
      >
        Analyse
      </button>
    );
  }
  if (need === "attribution" && !ask.attributed) {
    if (ask.hosted_pick === null || !ask.tools_offered.includes(ask.hosted_pick)) {
      return <span className="muted">no offered pick to explain</span>;
    }
    return (
      <button
        type="button"
        className="btn btn-secondary"
        disabled={busy || !ready}
        onClick={() => onStart(ask, "attribute")}
      >
        Attribute
      </button>
    );
  }
  return (
    <button type="button" className="btn btn-quiet" aria-pressed={selected} onClick={onShow}>
      {selected ? "Showing" : "Show"}
    </button>
  );
}

function StatusNote({ status }: { status: InterpStatus | undefined }) {
  if (!status) return null;
  if (!status.enabled) {
    return (
      <p className="lens-note">
        The local model is switched off on this deployment, so calls are listed but cannot be
        read. Set INTERP_ENABLED, INTERP_BASE_URL and INTERP_TOKEN, then start it with make
        interp.
      </p>
    );
  }
  if (!status.reachable) {
    return <p className="lens-note">The local model is switched on but not answering. {status.detail}</p>;
  }
  return (
    <p className="lens-note">
      Reading with {status.model} (revision {(status.revision ?? "").slice(0, 7)}) on{" "}
      {status.device}. Every reading and attribution is timed, priced by the clock and stored,
      so a second view is free.
    </p>
  );
}

/** A second, every second, while something runs; still otherwise. */
function useClock(ticking: boolean): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!ticking) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [ticking]);
  return now;
}

/** What to show under the table for the chosen call: a prompt, a wait, or the reading. */
export function ChosenReading({
  selected,
  loading,
  stored,
  children,
}: {
  selected: string | null;
  loading: boolean;
  stored: StoredAnalysis | null | undefined;
  children: (stored: StoredAnalysis) => ReactNode;
}) {
  if (selected === null) {
    return <p className="lens-note">Choose a captured call above to see its reading.</p>;
  }
  if (stored === undefined || (stored === null && loading)) {
    return <p className="lens-note">Loading the reading.</p>;
  }
  if (stored === null) {
    return <p className="lens-note">This call has not been read yet. Analyse it above.</p>;
  }
  return <>{children(stored)}</>;
}
