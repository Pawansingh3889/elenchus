"use client";

import Link from "next/link";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ErrorBanner } from "@/components/ErrorBanner";
import { axis, ChartCard, Gate, LensTooltip } from "@/components/lens/Chart";
import { Tile } from "@/components/lens/LensStripView";
import { percent, tokenCount } from "@/lib/lensFormat";
import { useLensScope } from "@/lib/lensScope";
import { useLensAttempts, useLensDecisions, useMe } from "@/lib/queries";
import type { AttemptRow, DecisionRow } from "@/lib/schemas";

/**
 * State: what the engine carries from turn to turn, and what carrying it costs. Every
 * call resends the system prompt and the transcript so far, so input grows with every
 * turn while the answers stay short.
 */
export default function StatePage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const [scope] = useLensScope();
  const attempts = useLensAttempts(scope, admin);
  const decisions = useLensDecisions(scope, admin);
  const rows = attempts.data ?? [];

  // One point per run and turn: the first call of the turn, which is the one that read
  // the transcript as the respondent left it.
  const runIds = [...new Set(rows.map((row) => row.run_id))];
  const focus = scope.runId ?? runIds[runIds.length - 1] ?? null;
  const turns = [...new Set(rows.map((row) => row.turn_number))].sort((a, b) => a - b);
  const firstOf = (run: string, turn: number) =>
    rows.find((row) => row.run_id === run && row.turn_number === turn && row.prompt_tokens !== null);
  const series = turns.map((turn) => {
    const point: Record<string, number | null> = { turn };
    for (const run of runIds) point[run] = firstOf(run, turn)?.prompt_tokens ?? null;
    return point;
  });

  const tokensIn = sum(rows.map((row) => row.prompt_tokens));
  const tokensOut = sum(rows.map((row) => row.completion_tokens));
  const cached = sum(rows.map((row) => row.cached_tokens));
  const focusRows = rows.filter((row) => row.run_id === focus);
  const firstTurn = focusRows.find((row) => row.prompt_tokens !== null)?.prompt_tokens ?? null;
  const lastTurn = [...focusRows].reverse().find((row) => row.prompt_tokens !== null)?.prompt_tokens ?? null;

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>State</h1>
        </div>
        <p className="lens-provenance">
          Measured per call. Input is what the model was sent: the system prompt, the briefing
          for the current question, and the transcript so far.
        </p>
        <ErrorBanner error={attempts.error ?? decisions.error} />

        <div className="lens-tiles">
          <Tile label="Share of tokens that are input" value={percent(tokensIn, tokensIn + tokensOut)} />
          <Tile label="Of the input, cached" value={percent(cached, tokensIn)} />
          <Tile label="Input on the first call" value={tokenCount(firstTurn)} />
          <Tile label="Input on the latest call" value={tokenCount(lastTurn)} />
        </div>

        <ChartCard
          title="Input tokens by turn"
          sample={`${runIds.length} run${runIds.length === 1 ? "" : "s"}, first call of each turn`}
          stale={attempts.isPlaceholderData}
          legend={
            runIds.length > 1
              ? [
                  { label: "Run in focus", color: "var(--series-1)" },
                  { label: "Other runs", color: "var(--border)" },
                ]
              : undefined
          }
          table={<GrowthTable rows={rows} />}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={series} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
              <CartesianGrid stroke="var(--border)" vertical={false} />
              <XAxis dataKey="turn" {...axis} allowDecimals={false} />
              <YAxis {...axis} width={56} tickFormatter={(v: number) => new Intl.NumberFormat("en-GB").format(v)} />
              <Tooltip
                content={(props) => (
                  <LensTooltip
                    {...props}
                    format={(v) => `${new Intl.NumberFormat("en-GB").format(v)} tokens`}
                    labelFormat={(label) => `Turn ${String(label)}`}
                  />
                )}
              />
              {runIds.map((run) => (
                <Line
                  key={run}
                  dataKey={run}
                  name={run === focus ? "Run in focus" : `Run ${run.slice(0, 8)}`}
                  stroke={run === focus ? "var(--series-1)" : "var(--border)"}
                  strokeWidth={2}
                  dot={{ r: 4, fill: run === focus ? "var(--series-1)" : "var(--border)", stroke: "var(--raised)", strokeWidth: 2 }}
                  connectNulls
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <section className="lens-section">
          <h2 className="lens-heading">What the engine knew at each ask</h2>
          <p className="lens-note">
            Blank means the ask was traced before the engine recorded that fact, which is
            unknown, not no.
          </p>
          <div className="lens-table-wrap">
            <StateTable rows={decisions.data ?? []} />
          </div>
        </section>
      </div>
    </Gate>
  );
}

function sum(values: (number | null)[]): number {
  return values.reduce<number>((total, value) => total + (value ?? 0), 0);
}

function yesNo(value: boolean | null): string {
  return value === null ? "" : value ? "yes" : "no";
}

function GrowthTable({ rows }: { rows: AttemptRow[] }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th>Run</th>
          <th className="num">Turn</th>
          <th className="num">Transcript messages</th>
          <th className="num">Tokens in</th>
          <th className="num">Cached</th>
          <th className="num">Tokens out</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id}>
            <td>
              <Link href={`/lens/runs/${row.run_id}`}>{row.run_id.slice(0, 8)}</Link>
            </td>
            <td className="num">{row.turn_number}</td>
            <td className="num">{row.transcript_messages ?? ""}</td>
            <td className="num">{tokenCount(row.prompt_tokens)}</td>
            <td className="num">{tokenCount(row.cached_tokens)}</td>
            <td className="num">{tokenCount(row.completion_tokens)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function StateTable({ rows }: { rows: DecisionRow[] }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th className="num">Turn</th>
          <th className="num">Question</th>
          <th>Answer type</th>
          <th>Follow-up policy</th>
          <th>Follow-up forced</th>
          <th>Follow-up awaiting reply</th>
          <th>Answer already recorded</th>
          <th>Recorded this turn</th>
          <th className="num">Follow-ups used</th>
          <th className="num">Replies used</th>
          <th className="num">Transcript</th>
          <th>Resolved to</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id}>
            <td className="num">
              {row.turn_number}
              {row.retry ? " (retry)" : ""}
            </td>
            <td className="num">{row.question_index === null ? "" : row.question_index + 1}</td>
            <td>{row.answer_type ?? ""}</td>
            <td>{row.follow_up_policy ?? ""}</td>
            <td>{yesNo(row.forced_probe)}</td>
            <td>{yesNo(row.probe_outstanding)}</td>
            <td>{yesNo(row.scripted_recorded)}</td>
            <td>{yesNo(row.recorded_this_turn)}</td>
            <td className="num">{row.follow_ups_used ?? ""}</td>
            <td className="num">{row.replies_used ?? ""}</td>
            <td className="num">{row.transcript_messages ?? ""}</td>
            <td>{row.resolved_to ?? "failed"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
