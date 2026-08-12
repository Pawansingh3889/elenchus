"use client";

import { Bar, BarChart, Cell, Tooltip, XAxis, YAxis } from "recharts";

import {
  CHART_AXIS,
  CHART_GRID,
  CHART_MARK,
  ChartContainer,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Card, CardLabel } from "@/components/ui/card";
import { useT } from "@/lib/i18n/useT";
import type { QuestionReport } from "@/lib/types";

/**
 * One question, as the whole survey answered it.
 *
 * The tally is a horizontal bar chart, and three of its choices are deliberate:
 *
 * - **Bars are a share of the largest count**, not of the number who answered, so a
 *   question where nobody agreed still reads as a shape rather than five slivers.
 * - **Every bar carries its count as text.** A tally is one series, so colour identifies
 *   nothing and a legend would label nothing; the number is the finding, and printing it
 *   is also what keeps the chart readable in greyscale and to a reader who cannot
 *   separate the hues.
 * - **Zero rows stay.** An option nobody picked is a finding, and a missing row reads as
 *   an option that was never offered.
 */
export function QuestionCard({
  question,
  position,
  children,
}: {
  question: QuestionReport;
  position: number;
  children?: React.ReactNode;
}) {
  const msg = useT();
  const rows = question.counts.map((c) => ({
    label: c.write_in ? `${c.label} ${msg.report.writeIn}` : c.label,
    count: c.count,
    writeIn: c.write_in,
  }));
  // Enough room per row to read the label, capped so a twenty-option question does not
  // become a page of its own.
  const height = Math.max(80, Math.min(rows.length * 34 + 24, 460));

  return (
    <Card className="p-4">
      <CardLabel>{msg.builder.questionLabel(position + 1)}</CardLabel>
      <h3 className="mt-1 text-md font-semibold">{question.text}</h3>
      <p className="mt-1 text-sm text-muted">
        {msg.report.answeredBy(question.answered)}
        {question.declined > 0 ? ` · ${msg.report.declinedBy(question.declined)}` : ""}
        {question.average !== null ? ` · ${msg.report.average(question.average.toFixed(1))}` : ""}
        {question.low !== null && question.high !== null && question.low !== question.high
          ? ` · ${msg.report.spread(question.low, question.high)}`
          : ""}
        {question.probed > 0 ? ` · ${msg.report.probedBy(question.probed)}` : ""}
      </p>

      {rows.length > 0 ? (
        <ChartContainer height={height} className="mt-3">
          <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 40, bottom: 4, left: 4 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="label"
              width={150}
              tickLine={false}
              axisLine={{ stroke: CHART_GRID }}
              tick={{ fill: CHART_AXIS }}
            />
            <Tooltip
              cursor={{ fill: CHART_GRID }}
              content={<ChartTooltipContent />}
            />
            <Bar
              dataKey="count"
              fill={CHART_MARK}
              radius={[0, 4, 4, 0]}
              label={{ position: "right", fill: CHART_AXIS, fontSize: 12 }}
              isAnimationActive={false}
            >
              {rows.map((row) => (
                // A write-in is the respondent's own words rather than an option the
                // author offered, so it is drawn in the lighter step of the same hue:
                // still one series, with the distinction carried by the "(write-in)" in
                // the label rather than by colour alone.
                <Cell
                  key={row.label}
                  fill={row.writeIn ? "var(--accent)" : CHART_MARK}
                />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      ) : null}

      {children}

      {question.answered === 0 && question.declined === 0 ? (
        <p className="mt-2 text-sm text-muted">{msg.report.noAnswers}</p>
      ) : null}
    </Card>
  );
}
