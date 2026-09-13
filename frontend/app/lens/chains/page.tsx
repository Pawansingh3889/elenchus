"use client";

import Link from "next/link";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ErrorBanner } from "@/components/ErrorBanner";
import { axis, ChartCard, Gate, LensTooltip } from "@/components/lens/Chart";
import { Tile } from "@/components/lens/LensStripView";
import { dollars, median, milliseconds, percent } from "@/lib/lensFormat";
import { useLensScope } from "@/lib/lensScope";
import { useLensDecisions, useMe } from "@/lib/queries";
import type { DecisionRow } from "@/lib/schemas";

type Chain = {
  runId: string;
  survey: string;
  question: number | null;
  answerType: string | null;
  asks: DecisionRow[];
};

/** Asks grouped by run, then by the question they were about, in the order they happened. */
function chainsOf(rows: DecisionRow[]): Chain[] {
  const chains = new Map<string, Chain>();
  for (const row of [...rows].sort((a, b) => Date.parse(a.started_at) - Date.parse(b.started_at))) {
    const key = `${row.run_id}:${row.question_index ?? "unknown"}`;
    const chain = chains.get(key);
    if (chain) {
      chain.asks.push(row);
      chain.answerType = chain.answerType ?? row.answer_type;
    } else {
      chains.set(key, {
        runId: row.run_id,
        survey: row.survey_title,
        question: row.question_index,
        answerType: row.answer_type,
        asks: [row],
      });
    }
  }
  return [...chains.values()];
}

function chainCost(chain: Chain): number | null {
  const priced = chain.asks.filter((ask) => ask.cost_usd !== null);
  return priced.length === 0 ? null : priced.reduce((total, ask) => total + (ask.cost_usd as number), 0);
}

/**
 * Cause chains: what happened to each question, ask by ask. A follow-up leads to the
 * answer it drew out; a refusal leads to the retry it caused; a give-up ends the chain with
 * no answer. The chain's cost is everything the question cost, so a long chain is visible
 * as money and time, not only as a count.
 */
export default function ChainsPage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const [scope] = useLensScope();
  const decisions = useLensDecisions(scope, admin);
  const chains = chainsOf(decisions.data ?? []);

  const followedUp = chains.filter((c) => c.asks.some((a) => a.resolved_to === "ask_follow_up"));
  const gaveUp = chains.filter((c) => c.asks.some((a) => a.resolved_to === "flag_unanswerable"));
  const refused = chains.filter((c) => c.asks.some((a) => a.outcome === "refused"));
  const byQuestion = [...new Set(chains.map((c) => c.question))]
    .filter((q): q is number => q !== null)
    .sort((a, b) => a - b)
    .map((question) => {
      const here = chains.filter((c) => c.question === question);
      return {
        question: `Q${question + 1}`,
        asks: here.reduce((total, c) => total + c.asks.length, 0) / here.length,
        runs: here.length,
      };
    });

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Cause chains</h1>
        </div>
        <p className="lens-provenance">
          Measured per ask and grouped per question. A chain is every ask the engine made about
          one question in one run, oldest first.
        </p>
        <ErrorBanner error={decisions.error} />

        <div className="lens-tiles">
          <Tile label="Question chains" value={String(chains.length)} />
          <Tile label="Median asks per question" value={String(median(chains.map((c) => c.asks.length)) ?? "no data")} />
          <Tile label="Needed a follow-up" value={`${followedUp.length} (${percent(followedUp.length, chains.length)})`} />
          <Tile label="Given up as unanswerable" value={`${gaveUp.length} (${percent(gaveUp.length, chains.length)})`} />
          <Tile label="Had a refusal" value={`${refused.length} (${percent(refused.length, chains.length)})`} />
        </div>

        <ChartCard
          title="Which questions need the longest chains"
          sample={`${chains.length} chains across ${new Set(chains.map((c) => c.runId)).size} runs; average asks per run`}
          stale={decisions.isPlaceholderData}
          table={
            <table className="lens-table">
              <thead>
                <tr>
                  <th>Question</th>
                  <th className="num">Runs</th>
                  <th className="num">Average asks</th>
                </tr>
              </thead>
              <tbody>
                {byQuestion.map((row) => (
                  <tr key={row.question}>
                    <td>{row.question}</td>
                    <td className="num">{row.runs}</td>
                    <td className="num">{row.asks.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          }
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={byQuestion} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
              <CartesianGrid stroke="var(--border)" vertical={false} />
              <XAxis dataKey="question" {...axis} />
              <YAxis {...axis} width={32} allowDecimals />
              <Tooltip
                cursor={{ fill: "var(--highlight-soft)" }}
                content={(props) => <LensTooltip {...props} format={(v) => `${v.toFixed(1)} asks on average`} />}
              />
              <Bar isAnimationActive={false} dataKey="asks" name="Average asks" fill="var(--series-1)" maxBarSize={24} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <section className="lens-section">
          <h2 className="lens-heading">Every chain</h2>
          <div className="lens-table-wrap">
            <table className="lens-table">
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Survey</th>
                  <th className="num">Question</th>
                  <th>Answer type</th>
                  <th>What happened, in order</th>
                  <th className="num">Asks</th>
                  <th className="num">Time</th>
                  <th className="num">Cost</th>
                </tr>
              </thead>
              <tbody>
                {chains.map((chain) => (
                  <tr key={`${chain.runId}-${chain.question}`}>
                    <td>
                      <Link href={`/lens/runs/${chain.runId}`}>{chain.runId.slice(0, 8)}</Link>
                    </td>
                    <td>{chain.survey}</td>
                    <td className="num">{chain.question === null ? "" : chain.question + 1}</td>
                    <td>{chain.answerType ?? ""}</td>
                    <td className="lens-wrap">
                      {chain.asks.map((ask, index) => (
                        <span key={ask.id}>
                          {index > 0 ? " → " : ""}
                          <span className={ask.outcome === "refused" ? "lens-refused" : undefined}>
                            {ask.retry ? "retry: " : ""}
                            {ask.picked ?? "no action"}
                            {ask.outcome === "refused" ? " (refused)" : ""}
                          </span>
                        </span>
                      ))}
                    </td>
                    <td className="num">{chain.asks.length}</td>
                    <td className="num">{milliseconds(chain.asks.reduce((total, ask) => total + ask.attempt_ms, 0))}</td>
                    <td className="num">{dollars(chainCost(chain))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </Gate>
  );
}
