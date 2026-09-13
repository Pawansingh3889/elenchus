"use client";

import Link from "next/link";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ErrorBanner } from "@/components/ErrorBanner";
import { axis, ChartCard, Gate, LensTooltip } from "@/components/lens/Chart";
import { Tile } from "@/components/lens/LensStripView";
import { dollars, median, milliseconds, moment, percent, tokenCount, TOO_FEW } from "@/lib/lensFormat";
import { useLensScope } from "@/lib/lensScope";
import { useLensAttempts, useMe } from "@/lib/queries";

/**
 * Inference: what one call to a model is made of. Most of a call's wait is the model
 * reading the prompt and thinking before it writes anything, so every call is split into
 * the time before its first token and the time spent writing.
 */
export default function InferencePage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const [scope] = useLensScope();
  const attempts = useLensAttempts(scope, admin);
  const rows = attempts.data ?? [];

  const split = rows.map((row, index) => ({
    key: `${index + 1}`,
    label: `turn ${row.turn_number}${row.retry ? ", retry" : ""} · ${row.model ?? "?"}`,
    waiting: row.first_token_ms ?? 0,
    writing: row.first_token_ms === null ? 0 : Math.max(0, row.duration_ms - row.first_token_ms),
    unsplit: row.first_token_ms === null ? row.duration_ms : 0,
  }));
  const timed = rows.filter((row) => row.first_token_ms !== null);
  const scatter = rows
    .filter((row) => row.first_token_ms !== null && row.prompt_tokens !== null)
    .map((row) => ({ prompt: row.prompt_tokens as number, first: row.first_token_ms as number }));
  const priced = rows.filter((row) => row.cost_usd !== null);

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Inference</h1>
        </div>
        <p className="lens-provenance">
          Measured per call. The wait before the first token is the model reading the prompt
          and thinking; the rest is writing. A call that did not stream has no split.
        </p>
        <ErrorBanner error={attempts.error} />

        <div className="lens-tiles">
          <Tile label="Calls" value={String(rows.length)} />
          <Tile label="Failed" value={`${rows.filter((r) => r.error !== null).length} (${percent(rows.filter((r) => r.error !== null).length, rows.length)})`} />
          <Tile label="Median wait for first token" value={milliseconds(median(timed.map((r) => r.first_token_ms as number)))} />
          <Tile label="Median writing" value={milliseconds(median(timed.map((r) => r.duration_ms - (r.first_token_ms as number))))} />
          <Tile label="Median tokens in" value={tokenCount(roundOrNull(median(rows.flatMap((r) => (r.prompt_tokens === null ? [] : [r.prompt_tokens])))))} />
          <Tile label="Median cost per call" value={dollars(median(priced.map((r) => r.cost_usd as number)))} />
        </div>

        <div className="lens-grid-2">
          <ChartCard
            title="Where each call's time went"
            sample={`${rows.length} calls, oldest first`}
            stale={attempts.isPlaceholderData}
            legend={[
              { label: "Before first token", color: "var(--series-1)" },
              { label: "Writing", color: "var(--series-2)" },
              { label: "Not split (did not stream)", color: "var(--series-3)" },
            ]}
            table={<AttemptTable rows={rows} />}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={split} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
                <CartesianGrid stroke="var(--border)" vertical={false} />
                <XAxis dataKey="key" {...axis} />
                <YAxis {...axis} tickFormatter={(v: number) => `${Math.round(v / 100) / 10}s`} width={44} />
                <Tooltip
                  cursor={{ fill: "var(--highlight-soft)" }}
                  content={(props) => (
                    <LensTooltip
                      {...props}
                      format={(v) => milliseconds(v)}
                      hideZero
                      labelFormat={(label) => split[Number(label) - 1]?.label ?? String(label)}
                    />
                  )}
                />
                <Bar isAnimationActive={false} dataKey="waiting" name="Before first token" stackId="t" fill="var(--series-1)" maxBarSize={24} stroke="var(--raised)" strokeWidth={2} />
                <Bar isAnimationActive={false} dataKey="writing" name="Writing" stackId="t" fill="var(--series-2)" maxBarSize={24} stroke="var(--raised)" strokeWidth={2} />
                <Bar isAnimationActive={false} dataKey="unsplit" name="Not split" stackId="t" fill="var(--series-3)" maxBarSize={24} radius={[4, 4, 0, 0]} stroke="var(--raised)" strokeWidth={2} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Does a longer prompt wait longer for its first token?"
            sample={
              scatter.length < TOO_FEW
                ? `${scatter.length} streamed calls: too few to read a trend from yet`
                : `${scatter.length} streamed calls`
            }
            stale={attempts.isPlaceholderData}
            table={<AttemptTable rows={rows} />}
          >
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
                <CartesianGrid stroke="var(--border)" />
                <XAxis type="number" dataKey="prompt" name="Tokens in" {...axis} domain={["auto", "auto"]} tickFormatter={(v: number) => new Intl.NumberFormat("en-GB").format(v)} />
                <YAxis type="number" dataKey="first" name="First token" {...axis} domain={["auto", "auto"]} tickFormatter={(v: number) => `${Math.round(v / 100) / 10}s`} width={44} />
                <Tooltip
                  cursor={{ stroke: "var(--border)" }}
                  content={(props) => (
                    <LensTooltip
                      {...props}
                      format={(v) => new Intl.NumberFormat("en-GB").format(v)}
                      labelFormat={() => "One call"}
                    />
                  )}
                />
                <Scatter isAnimationActive={false} data={scatter} fill="var(--series-1)" stroke="var(--raised)" strokeWidth={2} />
              </ScatterChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </div>
    </Gate>
  );
}

function roundOrNull(value: number | null): number | null {
  return value === null ? null : Math.round(value);
}

function AttemptTable({ rows }: { rows: ReturnType<typeof useLensAttempts>["data"] & object }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th>When</th>
          <th>Run</th>
          <th className="num">Turn</th>
          <th>Tier and model</th>
          <th className="num">Status</th>
          <th className="num">Tokens in (cached)</th>
          <th className="num">Tokens out</th>
          <th className="num">First token</th>
          <th className="num">Total</th>
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
            <td className="num">
              {row.turn_number}
              {row.retry ? " (retry)" : ""}
            </td>
            <td>
              tier {row.tier ?? "?"} · {row.model ?? "not reported"}
            </td>
            <td className="num">{row.status ?? "none"}</td>
            <td className="num">
              {tokenCount(row.prompt_tokens)} ({tokenCount(row.cached_tokens)})
            </td>
            <td className="num">{tokenCount(row.completion_tokens)}</td>
            <td className="num">{milliseconds(row.first_token_ms)}</td>
            <td className="num">{milliseconds(row.duration_ms)}</td>
            <td className="num">{dollars(row.cost_usd)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
