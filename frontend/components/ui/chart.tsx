"use client";

import * as React from "react";
import { ResponsiveContainer } from "recharts";

import { cn } from "@/lib/utils";

/* The charting seam. Recharts does the geometry; this file owns the two things a
   chart library will not decide for you.

   **The mark colour.** `--focus` rather than `--accent`: a bar is a mark, not
   decoration, and needs 3:1 against the surface it sits on. --accent measures 2.07:1
   on white and fails that; --focus clears it in both themes, measured rather than
   judged by eye. It is a token, so the dark palette swap in globals.css carries the
   chart with it.

   **What a tally chart is.** One series of counts, so there is no legend (a legend
   for one series labels nothing the title has not) and no colour-carried identity.
   Every bar is direct-labelled with its count, which is the convention the hand-rolled
   bars already used and is also what makes the chart readable in greyscale, in forced
   colours, and to a reader who cannot separate the hues at all. */

export const CHART_MARK = "var(--focus)";
export const CHART_GRID = "var(--border)";
export const CHART_AXIS = "var(--muted)";

export function ChartContainer({
  className,
  height = 220,
  children,
  ...props
}: Omit<React.ComponentProps<"div">, "children"> & {
  height?: number;
  children: React.ComponentProps<typeof ResponsiveContainer>["children"];
}) {
  return (
    <div
      className={cn(
        "w-full [&_.recharts-cartesian-axis-tick_text]:fill-muted",
        "[&_.recharts-cartesian-axis-tick_text]:text-xs",
        "[&_.recharts-surface]:overflow-visible",
        className,
      )}
      style={{ height }}
      {...props}
    >
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  );
}

/** A tooltip that wears the app's surface rather than Recharts' white default, which
 *  is invisible against the dark theme. */
export function ChartTooltipContent({
  active,
  payload,
  label,
  suffix,
  hint,
}: {
  active?: boolean;
  payload?: Array<{ value?: number | string; name?: string; payload?: Record<string, unknown> }>;
  label?: string;
  suffix?: string;
  /** A line under the value saying what a click will do, given the hovered row. A mark
   *  that acts on click has to say so somewhere, and the tooltip is the one place the
   *  reader is already looking when they are about to click it. */
  hint?: (row: Record<string, unknown>) => string | null;
}) {
  if (!active || !payload?.length) return null;
  const value = payload[0]?.value;
  const row = payload[0]?.payload;
  const line = hint && row ? hint(row) : null;
  return (
    <div className="rounded-lg border border-line bg-raised px-3 py-2 shadow-[var(--shadow-md)]">
      <div className="text-sm text-ink font-medium">{label}</div>
      <div className="text-sm text-muted">
        {value}
        {suffix ? ` ${suffix}` : ""}
      </div>
      {line ? <div className="mt-1 text-xs text-accent-strong">{line}</div> : null}
    </div>
  );
}
