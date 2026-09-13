"use client";

import type { ReactNode } from "react";

/**
 * The frame every lens chart sits in: a title that names what is plotted, a subtitle
 * with the sample size, the plot, and a table twin, because a chart is never the only
 * way to read a value.
 */
export function ChartCard({
  title,
  sample,
  stale,
  legend,
  table,
  children,
}: {
  title: string;
  sample: string;
  stale?: boolean;
  legend?: { label: string; color: string }[];
  table: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="lens-chart">
      <div>
        <h2 className="lens-chart-title">{title}</h2>
        <p className="lens-chart-sub">{sample}</p>
      </div>
      {legend && legend.length > 1 ? (
        <ul className="lens-legend" aria-label="Legend">
          {legend.map((item) => (
            <li key={item.label} className="lens-legend-item">
              <span className="lens-legend-swatch" style={{ background: item.color }} />
              {item.label}
            </li>
          ))}
        </ul>
      ) : null}
      <div className="lens-chart-plot" data-stale={stale ? "true" : "false"}>
        {children}
      </div>
      <details>
        <summary>Show as a table</summary>
        <div className="lens-table-wrap">{table}</div>
      </details>
    </section>
  );
}

type TooltipRow = { name?: string | number; value?: unknown; color?: string };

/** Values lead, names follow, a short line keys the series. Text wears text tokens. */
export function LensTooltip({
  active,
  payload,
  label,
  format,
  labelFormat,
  hideZero,
}: {
  active?: boolean;
  payload?: ReadonlyArray<TooltipRow>;
  label?: unknown;
  format: (value: number) => string;
  labelFormat?: (label: unknown) => string;
  /** For stacks, where a zero segment is not drawn and so is not a reading. A zero count
   *  on a grouped bar is a finding and must stay, so this is opt-in. */
  hideZero?: boolean;
}) {
  const rows = hideZero ? (payload ?? []).filter((row) => row.value !== 0) : (payload ?? []);
  if (!active || rows.length === 0) return null;
  return (
    <div className="lens-tooltip">
      <div className="lens-tooltip-label">
        {labelFormat ? labelFormat(label) : String(label ?? "")}
      </div>
      {rows.map((row, index) => (
        <div key={`${row.name}-${index}`} className="lens-tooltip-row">
          <span className="lens-tooltip-key" style={{ background: row.color }} />
          <span className="lens-tooltip-value">
            {typeof row.value === "number" ? format(row.value) : String(row.value ?? "")}
          </span>
          <span className="lens-tooltip-name">{row.name}</span>
        </div>
      ))}
    </div>
  );
}

/** Axis and grid chrome shared by every chart: recessive, hairline, solid. */
export const axis = {
  stroke: "var(--border)",
  tick: { fill: "var(--muted)", fontSize: 12 },
  tickLine: false,
} as const;

export function Gate({ admin, loading, children }: { admin: boolean; loading: boolean; children: ReactNode }) {
  if (loading) return <p className="empty">Loading…</p>;
  if (!admin) return <p className="empty">Sign in as an administrator to use the lens.</p>;
  return <>{children}</>;
}
