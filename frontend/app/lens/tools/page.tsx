"use client";

import Link from "next/link";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ErrorBanner } from "@/components/ErrorBanner";
import { axis, ChartCard, Gate, LensTooltip } from "@/components/lens/Chart";
import { Tile } from "@/components/lens/LensStripView";
import { dollars, milliseconds, percent } from "@/lib/lensFormat";
import { useLensScope } from "@/lib/lensScope";
import { useLensDecisions, useMe } from "@/lib/queries";
import type { DecisionRow } from "@/lib/schemas";

/**
 * Tool selection: at every ask the engine offers only the actions that are legal right
 * then, and the model picks one. How sure the model was is not measurable from the hosted
 * tier (it refuses logprobs), and arrives with the local model.
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
          chose; accepted is what the engine&rsquo;s check let through. How confident the model
          was arrives with the local model.
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
