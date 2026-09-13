"use client";

import Link from "next/link";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ErrorBanner } from "@/components/ErrorBanner";
import { axis, ChartCard, Gate, LensTooltip } from "@/components/lens/Chart";
import { Tile } from "@/components/lens/LensStripView";
import { probability } from "@/lib/interpFormat";
import { dollars, median, milliseconds, percent } from "@/lib/lensFormat";
import { useLensScope } from "@/lib/lensScope";
import { useInterpAsks, useLensDecisions, useMe } from "@/lib/queries";
import type { DecisionRow } from "@/lib/schemas";

/**
 * Tool selection: at every ask the engine offers only the actions that are legal right
 * then, and the model picks one. The hosted tier reports no probabilities, so how sure a
 * model is comes from Qwen3-0.6B reading the same captured prompt: a stand-in, shown with
 * how often it picks the same tool, never a measurement of the hosted model itself.
 */
export default function ToolsPage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const [scope] = useLensScope();
  const decisions = useLensDecisions(scope, admin);
  const rows = decisions.data ?? [];

  const tools = [...new Set(rows.flatMap((row) => [...row.tools_offered, ...(row.picked ? [row.picked] : [])]))].sort();
  const counts = tools.map((tool) => ({
    tool,
    offered: rows.filter((row) => row.tools_offered.includes(tool)).length,
    picked: rows.filter((row) => row.picked === tool).length,
    accepted: rows.filter((row) => row.picked === tool && row.outcome === "accepted").length,
  }));
  const single = rows.filter((row) => row.tools_offered.length === 1).length;

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Tool selection</h1>
        </div>
        <p className="lens-provenance">
          Measured per ask. Offered is what the engine allowed; picked is what the model
          chose; accepted is what the engine&rsquo;s check let through. How sure a local model
          is, reading the same prompt, is at the foot of the page.
        </p>
        <ErrorBanner error={decisions.error} />

        <div className="lens-tiles">
          <Tile label="Asks" value={String(rows.length)} />
          <Tile label="Retries" value={`${rows.filter((r) => r.retry).length} (${percent(rows.filter((r) => r.retry).length, rows.length)})`} />
          <Tile label="Asks with one choice" value={`${single} (${percent(single, rows.length)})`} />
          <Tile label="Picked something not offered" value={String(rows.filter((r) => r.picked !== null && !r.tools_offered.includes(r.picked)).length)} />
        </div>

        <ChartCard
          title="Offered, picked and accepted, per tool"
          sample={`${rows.length} asks`}
          stale={decisions.isPlaceholderData}
          legend={[
            { label: "Offered", color: "var(--series-1)" },
            { label: "Picked", color: "var(--series-2)" },
            { label: "Accepted", color: "var(--series-3)" },
          ]}
          table={<CountTable counts={counts} />}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={counts} layout="vertical" margin={{ top: 8, right: 16, bottom: 0, left: 8 }} barGap={2}>
              <CartesianGrid stroke="var(--border)" horizontal={false} />
              <XAxis type="number" {...axis} allowDecimals={false} />
              <YAxis type="category" dataKey="tool" {...axis} width={140} />
              <Tooltip
                cursor={{ fill: "var(--highlight-soft)" }}
                content={(props) => <LensTooltip {...props} format={(v) => `${v} asks`} />}
              />
              <Bar isAnimationActive={false} dataKey="offered" name="Offered" fill="var(--series-1)" maxBarSize={12} radius={[0, 4, 4, 0]} />
              <Bar isAnimationActive={false} dataKey="picked" name="Picked" fill="var(--series-2)" maxBarSize={12} radius={[0, 4, 4, 0]} />
              <Bar isAnimationActive={false} dataKey="accepted" name="Accepted" fill="var(--series-3)" maxBarSize={12} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <section className="lens-section">
          <h2 className="lens-heading">Every ask</h2>
          <div className="lens-table-wrap">
            <AskTable rows={rows} />
          </div>
        </section>

        <Confidence admin={admin} />
      </div>
    </Gate>
  );
}

function CountTable({ counts }: { counts: { tool: string; offered: number; picked: number; accepted: number }[] }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th>Tool</th>
          <th className="num">Offered</th>
          <th className="num">Picked</th>
          <th className="num">Accepted</th>
        </tr>
      </thead>
      <tbody>
        {counts.map((row) => (
          <tr key={row.tool}>
            <td>{row.tool}</td>
            <td className="num">{row.offered}</td>
            <td className="num">{row.picked}</td>
            <td className="num">{row.accepted}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function AskTable({ rows }: { rows: DecisionRow[] }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th>Run</th>
          <th className="num">Turn</th>
          <th>Offered</th>
          <th>Picked</th>
          <th>Check</th>
          <th>Resolved to</th>
          <th className="num">Took</th>
          <th className="num">Cost</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id}>
            <td>
              <Link href={`/lens/runs/${row.run_id}`}>{row.run_id.slice(0, 8)}</Link>
            </td>
            <td className="num">
              {row.turn_number}
              {row.retry ? " (retry)" : ""}
            </td>
            <td>{row.tools_offered.join(", ")}</td>
            <td>{row.picked ?? "nothing to check"}</td>
            <td className={row.outcome === "refused" ? "lens-refused" : undefined}>{row.outcome ?? ""}</td>
            <td>{row.resolved_to ?? "failed"}</td>
            <td className="num">{milliseconds(row.attempt_ms)}</td>
            <td className="num">{dollars(row.cost_usd)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** How sure Qwen3-0.6B is of the hosted pick, over the captured calls it has read. */
function Confidence({ admin }: { admin: boolean }) {
  const [scope] = useLensScope();
  const asks = useInterpAsks(scope, admin);
  const captured = asks.data ?? [];
  const read = captured.filter(
    (ask) => ask.analysed && ask.qwen_probability_of_hosted_pick !== null,
  );
  const agreeing = read.filter((ask) => ask.agrees === true).length;
  // A median over the read calls with this check, or words when there are none: no refused
  // pick is a fact about the calls, not a confidence of zero.
  const sureOf = (outcome: string) => {
    const scores = read.flatMap((ask) =>
      ask.outcome === outcome && ask.qwen_probability_of_hosted_pick !== null
        ? [ask.qwen_probability_of_hosted_pick]
        : [],
    );
    return scores.length === 0 ? `none ${outcome}` : probability(median(scores));
  };

  return (
    <section className="lens-section">
      <h2 className="lens-heading">How sure a local model is of the hosted pick</h2>
      <p className="lens-note">
        Qwen3-0.6B reading the exact prompt of each captured call. Calls are read one at a time
        from the Hidden layers page.
      </p>
      <ErrorBanner error={asks.error} />
      <div className="lens-tiles">
        <Tile label="Captured calls" value={String(captured.length)} />
        <Tile label="Read by the local model" value={String(read.length)} />
        <Tile
          label="Picks the same tool"
          value={`${agreeing} of ${read.length} (${percent(agreeing, read.length)})`}
        />
        <Tile label="Median confidence, accepted picks" value={sureOf("accepted")} />
        <Tile label="Median confidence, refused picks" value={sureOf("refused")} />
      </div>
      <div className="lens-table-wrap">
        <table className="lens-table">
          <thead>
            <tr>
              <th>Run</th>
              <th>Hosted pick</th>
              <th>Check</th>
              <th>Qwen&rsquo;s pick</th>
              <th className="num">Qwen on the hosted pick</th>
              <th className="num">Reading</th>
            </tr>
          </thead>
          <tbody>
            {read.map((ask) => (
              <tr key={ask.span_id}>
                <td>
                  <Link href={`/lens/hidden-layers?ask=${ask.span_id}`}>{ask.run_id.slice(0, 8)}</Link>
                </td>
                <td>{ask.hosted_pick}</td>
                <td className={ask.outcome === "refused" ? "lens-refused" : undefined}>{ask.outcome ?? ""}</td>
                <td>{ask.qwen_pick}</td>
                <td className="num">{probability(ask.qwen_probability_of_hosted_pick)}</td>
                <td className="num">
                  {milliseconds(ask.analysis_ms)} · {dollars(ask.analysis_cost_usd)}
                </td>
              </tr>
            ))}
            {read.length === 0 ? (
              <tr>
                <td colSpan={6} className="muted">
                  No captured call in this scope has been read yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
