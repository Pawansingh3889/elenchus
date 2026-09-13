"use client";

import { useState } from "react";
import {
  CartesianGrid,
  ResponsiveContainer,
  Sankey,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ErrorBanner } from "@/components/ErrorBanner";
import { axis, ChartCard, Gate, LensTooltip } from "@/components/lens/Chart";
import { useLensScope } from "@/lib/lensScope";
import { useLensAttempts, useLensCorrelations, useLensDecisions, useMe } from "@/lib/queries";
import type { AttemptRow, CorrelationCell, DecisionRow } from "@/lib/schemas";

const LABELS: Record<string, string> = {
  tokens_in: "Tokens in",
  cached_tokens: "Cached tokens",
  tokens_out: "Tokens out",
  transcript_messages: "Transcript length",
  turn_number: "Turn number",
  retry: "Was a retry",
  first_token_ms: "Wait for first token",
  writing_ms: "Writing time",
  duration_ms: "Total time",
  cost_usd: "Cost",
};

const READ: Record<string, (row: AttemptRow) => number | null> = {
  tokens_in: (r) => r.prompt_tokens,
  cached_tokens: (r) => r.cached_tokens,
  tokens_out: (r) => r.completion_tokens,
  transcript_messages: (r) => r.transcript_messages,
  turn_number: (r) => r.turn_number,
  retry: (r) => (r.retry ? 1 : 0),
  first_token_ms: (r) => r.first_token_ms,
  writing_ms: (r) => (r.first_token_ms === null ? null : r.duration_ms - r.first_token_ms),
  duration_ms: (r) => r.duration_ms,
  cost_usd: (r) => r.cost_usd,
};

// Joins the stages of one path into a map key. Stage labels never contain it.
const STAGE_SEPARATOR = " >> ";

/**
 * Relationships: which factors move with cost and latency, and how asks flow from what was
 * asked to what the engine did. Correlation over real traffic, not cause: a longer
 * transcript is also a later turn, and this page cannot separate the two.
 */
export default function RelationshipsPage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const [scope] = useLensScope();
  const matrix = useLensCorrelations(scope, admin);
  const attempts = useLensAttempts(scope, admin);
  const decisions = useLensDecisions(scope, admin);
  const [picked, setPicked] = useState<{ factor: string; outcome: string } | null>(null);

  const cells = matrix.data?.cells ?? [];
  const cellOf = (factor: string, outcome: string) =>
    cells.find((c) => c.factor === factor && c.outcome === outcome);
  const chosen = picked ?? (matrix.data ? { factor: "tokens_in", outcome: "first_token_ms" } : null);
  const points = chosen
    ? (attempts.data ?? []).flatMap((row) => {
        const x = READ[chosen.factor](row);
        const y = READ[chosen.outcome](row);
        return x === null || y === null ? [] : [{ x, y }];
      })
    : [];
  const chosenCell = chosen ? cellOf(chosen.factor, chosen.outcome) : undefined;

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Relationships</h1>
        </div>
        <p className="lens-provenance">
          Spearman rank correlation per call, with a 95% bootstrap interval. Below{" "}
          {matrix.data?.min_samples ?? 20} calls a cell is outlined and uncoloured: shown for
          reference, never a finding. Correlation, not cause.
        </p>
        <ErrorBanner error={matrix.error ?? attempts.error ?? decisions.error} />

        {matrix.data ? (
          <section className="lens-section">
            <h2 className="lens-heading">What moves with cost and latency</h2>
            <div className="lens-table-wrap">
              <table className="lens-table lens-matrix">
                <thead>
                  <tr>
                    <th scope="col">Factor</th>
                    {matrix.data.outcomes.map((outcome) => (
                      <th key={outcome} scope="col">
                        {LABELS[outcome] ?? outcome}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {matrix.data.factors.map((factor) => (
                    <tr key={factor}>
                      <th scope="row">{LABELS[factor] ?? factor}</th>
                      {matrix.data.outcomes.map((outcome) => {
                        const cell = cellOf(factor, outcome);
                        return (
                          <td key={outcome}>
                            {cell ? (
                              <CellButton
                                cell={cell}
                                pressed={chosen?.factor === factor && chosen?.outcome === outcome}
                                onPick={() => setPicked({ factor, outcome })}
                              />
                            ) : null}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        <div className="lens-grid-2">
          {chosen ? (
            <ChartCard
              title={`${LABELS[chosen.factor]} against ${LABELS[chosen.outcome].toLowerCase()}`}
              sample={`${points.length} calls${chosenCell?.too_few ? ": too few to call it a relationship" : ""}`}
              stale={attempts.isPlaceholderData}
              table={<PointsTable points={points} factor={chosen.factor} outcome={chosen.outcome} />}
            >
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
                  <CartesianGrid stroke="var(--border)" />
                  <XAxis type="number" dataKey="x" name={LABELS[chosen.factor]} domain={["auto", "auto"]} {...axis} />
                  <YAxis type="number" dataKey="y" name={LABELS[chosen.outcome]} domain={["auto", "auto"]} {...axis} width={60} />
                  <Tooltip
                    cursor={{ stroke: "var(--border)" }}
                    content={(props) => (
                      <LensTooltip
                        {...props}
                        format={(v) => new Intl.NumberFormat("en-GB", { maximumFractionDigits: 4 }).format(v)}
                        labelFormat={() => "One call"}
                      />
                    )}
                  />
                  <Scatter isAnimationActive={false} data={points} fill="var(--series-1)" stroke="var(--raised)" strokeWidth={2} />
                </ScatterChart>
              </ResponsiveContainer>
            </ChartCard>
          ) : null}
          <FlowCard rows={decisions.data} stale={decisions.isPlaceholderData} />
        </div>
      </div>
    </Gate>
  );
}

function CellButton({ cell, pressed, onPick }: { cell: CorrelationCell; pressed: boolean; onPick: () => void }) {
  const strength = cell.rho === null ? 0 : Math.abs(cell.rho);
  const pole = cell.rho !== null && cell.rho < 0 ? "var(--div-neg)" : "var(--div-pos)";
  const coloured = !cell.too_few && cell.rho !== null;
  const className = ["lens-cell", coloured ? "" : "lens-cell-few", coloured && strength > 0.6 ? "lens-cell-strong" : ""]
    .filter(Boolean)
    .join(" ");
  return (
    <button
      type="button"
      className={className}
      style={coloured ? { background: `color-mix(in oklab, ${pole} ${Math.round(strength * 100)}%, var(--div-mid))` } : undefined}
      aria-pressed={pressed}
      onClick={onPick}
    >
      <span className="lens-cell-rho">
        {cell.rho === null ? (cell.no_variation ? "no variation" : "no data") : cell.rho.toFixed(2)}
      </span>
      <span className="lens-cell-ci">
        {cell.ci_low === null || cell.ci_high === null
          ? cell.too_few
            ? "too few"
            : "no interval"
          : `${cell.ci_low.toFixed(2)} to ${cell.ci_high.toFixed(2)}`}
      </span>
      <span className="lens-cell-n">n = {cell.n}</span>
    </button>
  );
}

function PointsTable({ points, factor, outcome }: { points: { x: number; y: number }[]; factor: string; outcome: string }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th className="num">{LABELS[factor]}</th>
          <th className="num">{LABELS[outcome]}</th>
        </tr>
      </thead>
      <tbody>
        {points.map((point, index) => (
          <tr key={index}>
            <td className="num">{point.x}</td>
            <td className="num">{point.y}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Answer type, then the tool the model picked, then the check, then what the ask resolved to. */
function FlowCard({ rows, stale }: { rows: DecisionRow[] | undefined; stale: boolean }) {
  const paths = new Map<string, number>();
  for (const row of rows ?? []) {
    const key = [
      `type: ${row.answer_type ?? "not recorded"}`,
      `picked: ${row.picked ?? "nothing"}`,
      `check: ${row.outcome ?? "none"}`,
      `resolved: ${row.resolved_to ?? "failed"}`,
    ].join(STAGE_SEPARATOR);
    paths.set(key, (paths.get(key) ?? 0) + 1);
  }
  const names: string[] = [];
  const indexOf = (name: string) => {
    const at = names.indexOf(name);
    if (at >= 0) return at;
    names.push(name);
    return names.length - 1;
  };
  const links = new Map<string, number>();
  for (const [key, value] of paths) {
    const stages = key.split(STAGE_SEPARATOR);
    for (let i = 0; i < stages.length - 1; i++) {
      // Stages carry their prefix, so "picked: record_answer" and "resolved: record_answer"
      // are different nodes and the diagram cannot loop back on itself.
      const link = `${indexOf(stages[i])}:${indexOf(stages[i + 1])}`;
      links.set(link, (links.get(link) ?? 0) + value);
    }
  }
  const data = {
    nodes: names.map((name) => ({ name })),
    links: [...links].map(([link, value]) => {
      const [source, target] = link.split(":").map(Number);
      return { source, target, value };
    }),
  };

  return (
    <ChartCard
      title="How asks flow: answer type, then pick, then check, then outcome"
      sample={rows === undefined ? "Loading asks" : `${rows.length} asks`}
      stale={stale}
      table={
        <table className="lens-table">
          <thead>
            <tr>
              <th>Answer type</th>
              <th>Picked</th>
              <th>Check</th>
              <th>Resolved to</th>
              <th className="num">Asks</th>
            </tr>
          </thead>
          <tbody>
            {[...paths]
              .sort((a, b) => b[1] - a[1])
              .map(([key, value]) => (
                <tr key={key}>
                  {key.split(STAGE_SEPARATOR).map((stage) => (
                    <td key={stage}>{stage.split(": ").slice(1).join(": ")}</td>
                  ))}
                  <td className="num">{value}</td>
                </tr>
              ))}
          </tbody>
        </table>
      }
    >
      {data.links.length > 0 ? (
        <ResponsiveContainer width="100%" height="100%">
          <Sankey
            data={data}
            nodePadding={14}
            nodeWidth={10}
            margin={{ top: 8, right: 170, bottom: 8, left: 8 }}
            link={{ stroke: "var(--series-1)", strokeOpacity: 0.25 }}
            node={<FlowNode />}
          >
            <Tooltip content={(props) => <LensTooltip {...props} format={(v) => `${v} asks`} />} />
          </Sankey>
        </ResponsiveContainer>
      ) : (
        // Undefined is still loading, which is not the same finding as an empty scope.
        <p className="lens-note">{rows === undefined ? "Loading…" : "No asks in this scope."}</p>
      )}
    </ChartCard>
  );
}

function FlowNode(props: { x?: number; y?: number; width?: number; height?: number; payload?: { name?: string } }) {
  const { x = 0, y = 0, width = 0, height = 0, payload } = props;
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} fill="var(--series-1)" rx={2} />
      {/* The stage prefix is dropped: the card title names the stages left to right. The
          halo in the card's colour keeps a label legible where it crosses a link. */}
      <text
        x={x + width + 6}
        y={y + height / 2}
        dy="0.35em"
        fontSize={12}
        fill="var(--ink)"
        stroke="var(--raised)"
        strokeWidth={4}
        paintOrder="stroke"
        strokeLinejoin="round"
      >
        {(payload?.name ?? "").split(": ").slice(1).join(": ")}
      </text>
    </g>
  );
}
