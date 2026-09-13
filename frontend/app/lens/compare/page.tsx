"use client";

import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ErrorBanner } from "@/components/ErrorBanner";
import { axis, ChartCard, Gate, LensTooltip } from "@/components/lens/Chart";
import { Tile } from "@/components/lens/LensStripView";
import { dollars, median, milliseconds } from "@/lib/lensFormat";
import { useLensAttempts, useLensDecisions, useLensRuns, useMe } from "@/lib/queries";
import type { AttemptRow, DecisionRow, TracedRun } from "@/lib/schemas";

/** One run's figures per question, so two runs of the same survey can be read side by side. */
function perQuestion(decisions: DecisionRow[]) {
  const rows = new Map<number, { asks: number; followUps: number; gaveUp: number; ms: number; cost: number | null }>();
  for (const ask of decisions) {
    if (ask.question_index === null) continue;
    const row = rows.get(ask.question_index) ?? { asks: 0, followUps: 0, gaveUp: 0, ms: 0, cost: null };
    row.asks += 1;
    row.followUps += ask.resolved_to === "ask_follow_up" ? 1 : 0;
    row.gaveUp += ask.resolved_to === "flag_unanswerable" ? 1 : 0;
    row.ms += ask.attempt_ms;
    if (ask.cost_usd !== null) row.cost = (row.cost ?? 0) + ask.cost_usd;
    rows.set(ask.question_index, row);
  }
  return rows;
}

/**
 * Compare runs: two runs, question by question. Most useful on two runs of the same survey,
 * where the questions line up and the difference is the respondent, the language, or the
 * prompt version that was live.
 */
export default function ComparePage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const runs = useLensRuns(admin);
  const all = runs.data ?? [];
  const [left, setLeft] = useState<string | null>(null);
  const [right, setRight] = useState<string | null>(null);
  const a = left ?? all[1]?.run_id ?? null;
  const b = right ?? all[0]?.run_id ?? null;

  const aAttempts = useLensAttempts({ surveyId: null, runId: a }, admin && a !== null);
  const bAttempts = useLensAttempts({ surveyId: null, runId: b }, admin && b !== null);
  const aDecisions = useLensDecisions({ surveyId: null, runId: a }, admin && a !== null);
  const bDecisions = useLensDecisions({ surveyId: null, runId: b }, admin && b !== null);

  const aRows = perQuestion(aDecisions.data ?? []);
  const bRows = perQuestion(bDecisions.data ?? []);
  const questions = [...new Set([...aRows.keys(), ...bRows.keys()])].sort((x, y) => x - y);
  const chart = questions.map((q) => ({
    question: `Q${q + 1}`,
    a: aRows.get(q)?.cost ?? 0,
    b: bRows.get(q)?.cost ?? 0,
  }));
  const runA = all.find((run) => run.run_id === a);
  const runB = all.find((run) => run.run_id === b);

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Compare runs</h1>
        </div>
        <p className="lens-provenance">
          Measured per ask. Questions line up by position, so compare two runs of the same survey
          for a like-for-like reading.
        </p>
        <ErrorBanner error={runs.error ?? aDecisions.error ?? bDecisions.error ?? aAttempts.error ?? bAttempts.error} />

        <div className="lens-filters">
          <RunPicker label="Run A" runs={all} value={a} onChange={setLeft} />
          <RunPicker label="Run B" runs={all} value={b} onChange={setRight} />
        </div>

        <div className="lens-grid-2">
          <RunTiles label="Run A" run={runA} attempts={aAttempts.data ?? []} />
          <RunTiles label="Run B" run={runB} attempts={bAttempts.data ?? []} />
        </div>

        <ChartCard
          title="Cost per question"
          sample={`${questions.length} questions; ${runA?.survey_title ?? "?"} against ${runB?.survey_title ?? "?"}`}
          legend={[
            { label: "Run A", color: "var(--series-1)" },
            { label: "Run B", color: "var(--series-2)" },
          ]}
          table={
            <table className="lens-table">
              <thead>
                <tr>
                  <th>Question</th>
                  <th className="num">Asks A / B</th>
                  <th className="num">Follow-ups A / B</th>
                  <th className="num">Gave up A / B</th>
                  <th className="num">Time A / B</th>
                  <th className="num">Cost A / B</th>
                </tr>
              </thead>
              <tbody>
                {questions.map((q) => {
                  const x = aRows.get(q);
                  const y = bRows.get(q);
                  return (
                    <tr key={q}>
                      <td>Q{q + 1}</td>
                      <td className="num">{x?.asks ?? 0} / {y?.asks ?? 0}</td>
                      <td className="num">{x?.followUps ?? 0} / {y?.followUps ?? 0}</td>
                      <td className="num">{x?.gaveUp ?? 0} / {y?.gaveUp ?? 0}</td>
                      <td className="num">{milliseconds(x?.ms ?? null)} / {milliseconds(y?.ms ?? null)}</td>
                      <td className="num">{dollars(x?.cost ?? null)} / {dollars(y?.cost ?? null)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          }
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart} margin={{ top: 8, right: 8, bottom: 0, left: 8 }} barGap={2}>
              <CartesianGrid stroke="var(--border)" vertical={false} />
              <XAxis dataKey="question" {...axis} />
              <YAxis {...axis} width={56} tickFormatter={(v: number) => `$${v.toFixed(3)}`} />
              <Tooltip cursor={{ fill: "var(--highlight-soft)" }} content={(props) => <LensTooltip {...props} format={(v) => dollars(v)} />} />
              <Bar isAnimationActive={false} dataKey="a" name="Run A" fill="var(--series-1)" maxBarSize={24} radius={[4, 4, 0, 0]} />
              <Bar isAnimationActive={false} dataKey="b" name="Run B" fill="var(--series-2)" maxBarSize={24} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </Gate>
  );
}

function RunPicker({
  label,
  runs,
  value,
  onChange,
}: {
  label: string;
  runs: TracedRun[];
  value: string | null;
  onChange: (id: string | null) => void;
}) {
  return (
    <label className="lens-filter">
      <span>{label}</span>
      <select value={value ?? ""} onChange={(e) => onChange(e.target.value || null)}>
        {runs.map((run) => (
          <option key={run.run_id} value={run.run_id}>
            {run.survey_title} · {run.turns} turns · {run.run_id.slice(0, 8)}
          </option>
        ))}
      </select>
    </label>
  );
}

function RunTiles({ label, run, attempts }: { label: string; run: TracedRun | undefined; attempts: AttemptRow[] }) {
  const firstTokens = attempts.flatMap((row) => (row.first_token_ms === null ? [] : [row.first_token_ms]));
  return (
    <section className="lens-section">
      <h2 className="lens-heading">{label}: {run?.survey_title ?? "no run picked"}</h2>
      <div className="lens-tiles">
        <Tile label="Turns" value={String(run?.turns ?? 0)} />
        <Tile label="Calls" value={String(attempts.length)} />
        <Tile label="Cost" value={dollars(run?.cost_usd ?? null, run?.unmetered_attempts ?? 0)} />
        <Tile label="Median first token" value={milliseconds(median(firstTokens))} />
      </div>
    </section>
  );
}
