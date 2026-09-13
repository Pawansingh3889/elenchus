"use client";

import Link from "next/link";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ErrorBanner } from "@/components/ErrorBanner";
import { axis, ChartCard, Gate, LensTooltip } from "@/components/lens/Chart";
import { Tile } from "@/components/lens/LensStripView";
import { dollars, milliseconds, moment, percent } from "@/lib/lensFormat";
import { useLensScope } from "@/lib/lensScope";
import { useLensDecisions, useMe } from "@/lib/queries";
import type { DecisionRow } from "@/lib/schemas";

/**
 * Validation: the engine re-checks every action the model picks, in code, before acting
 * on it. A refusal costs a retry; an answer given up as unanswerable costs the answer.
 * Both are shown with what they cost, because that is the trade the checks make.
 */
export default function ValidationPage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const [scope] = useLensScope();
  const decisions = useLensDecisions(scope, admin);
  const rows = decisions.data ?? [];

  const checked = rows.filter((row) => row.outcome !== null);
  const refused = rows.filter((row) => row.outcome === "refused");
  const gaveUp = rows.filter((row) => row.picked === "flag_unanswerable" && row.outcome === "accepted");
  // Null only when there were refusals and none of them was priced: no refusals is $0.
  const refusedCost =
    refused.length === 0
      ? 0
      : refused.reduce<number | null>(
          (total, row) => (row.cost_usd === null ? total : (total ?? 0) + row.cost_usd),
          null,
        );
  const byTool = [...new Set(refused.map((row) => row.picked ?? "unknown"))].map((tool) => ({
    tool,
    refused: refused.filter((row) => (row.picked ?? "unknown") === tool).length,
  }));

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Validation</h1>
        </div>
        <p className="lens-provenance">
          Measured per ask. A refusal&rsquo;s cost is its own call, not the retry it caused; the
          retry is counted on its own row.
        </p>
        <ErrorBanner error={decisions.error} />

        <div className="lens-tiles">
          <Tile label="Actions checked" value={String(checked.length)} />
          <Tile label="Refused" value={`${refused.length} (${percent(refused.length, checked.length)})`} />
          <Tile label="Spent on refused calls" value={dollars(refusedCost)} />
          <Tile label="Time on refused calls" value={milliseconds(refused.reduce((total, row) => total + row.attempt_ms, 0))} />
          <Tile label="Answers given up as unanswerable" value={String(gaveUp.length)} />
          <Tile label="Asks with no action to check" value={String(rows.length - checked.length)} />
        </div>

        {refused.length > 0 ? (
          <ChartCard
            title="Refusals by the tool the model picked"
            sample={`${refused.length} refusals`}
            stale={decisions.isPlaceholderData}
            table={<RefusalTable rows={refused} />}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byTool} layout="vertical" margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
                <CartesianGrid stroke="var(--border)" horizontal={false} />
                <XAxis type="number" {...axis} allowDecimals={false} />
                <YAxis type="category" dataKey="tool" {...axis} width={140} />
                <Tooltip
                  cursor={{ fill: "var(--highlight-soft)" }}
                  content={(props) => <LensTooltip {...props} format={(v) => `${v} refused`} />}
                />
                <Bar isAnimationActive={false} dataKey="refused" name="Refused" fill="var(--series-1)" maxBarSize={24} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        ) : (
          <p className="lens-note">No refusals in this scope. Every action the model picked was accepted.</p>
        )}

        <section className="lens-section">
          <h2 className="lens-heading">Answers given up as unanswerable</h2>
          <p className="lens-note">
            Accepted by the check, and still worth reading: an answer that held an opinion but
            no number is recorded as none.
          </p>
          <div className="lens-table-wrap">
            <RefusalTable rows={gaveUp} />
          </div>
        </section>
      </div>
    </Gate>
  );
}

function RefusalTable({ rows }: { rows: DecisionRow[] }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th>When</th>
          <th>Run</th>
          <th className="num">Turn</th>
          <th>Answer type</th>
          <th>Picked</th>
          <th>Check</th>
          <th>Reason</th>
          <th>Resolved to</th>
          <th className="num">Cost</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id}>
            <td>{moment(row.started_at)}</td>
            <td>
              <Link href={`/lens/runs/${row.run_id}`}>{row.run_id.slice(0, 8)}</Link>
            </td>
            <td className="num">{row.turn_number}</td>
            <td>{row.answer_type ?? ""}</td>
            <td>{row.picked ?? ""}</td>
            <td className={row.outcome === "refused" ? "lens-refused" : undefined}>{row.outcome ?? ""}</td>
            <td>{row.reason ?? ""}</td>
            <td>{row.resolved_to ?? "failed"}</td>
            <td className="num">{dollars(row.cost_usd)}</td>
          </tr>
        ))}
        {rows.length === 0 ? (
          <tr>
            <td colSpan={9} className="muted">
              None in this scope.
            </td>
          </tr>
        ) : null}
      </tbody>
    </table>
  );
}
