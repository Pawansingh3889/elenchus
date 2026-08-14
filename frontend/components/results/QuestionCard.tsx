"use client";

import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

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
 * **The form follows the answer type**, one each, chosen for what the data is rather
 * than offered as a menu: a tally of options is a bar chart, a yes/no is two parts of
 * one whole and so a donut, and a rating is a fixed 1-5 scale whose shape matters, so it
 * stands up with its average marked on it. No card carries two forms of the same
 * numbers; a toggle would only invite a reader to pick the misleading one, and a donut
 * of a multi-select is exactly that, since its slices add past a hundred.
 *
 * The rest holds across all three:
 *
 * - **Bars are a share of the largest count**, not of the number who answered, so a
 *   question where nobody agreed still reads as a shape rather than five slivers.
 * - **Every mark carries its count and its share as text.** A tally is one series, so
 *   colour identifies nothing and a legend would label nothing; the numbers are the
 *   finding, and printing them is also what keeps the chart readable in greyscale and to
 *   a reader who cannot separate the hues.
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
  const multi = question.answer_type === "multi_select";
  // Two denominators, and only a multi-select needs both. `answered` is people and
  // `selections` is picks; on every other type they are the same number, because one
  // person makes one choice. Showing a single percentage on a multi-select is how a
  // question gets quoted wrongly: "84% chose Facebook" and "17% of picks were Facebook"
  // are both true of the same column.
  const people = question.answered;
  const picks = question.selections;
  const share = (count: number, of: number) => (of > 0 ? `${Math.round((count / of) * 1000) / 10}%` : "-");

  const rows = question.counts.map((c) => ({
    label: c.write_in ? `${c.label} ${msg.report.writeIn}` : c.label,
    count: c.count,
    writeIn: c.write_in,
    // The label printed at the end of the mark: the count, then its share of people,
    // then on a multi-select its share of the picks as well.
    marked: multi
      ? `${c.count}  ${share(c.count, people)} · ${share(c.count, picks)}`
      : `${c.count}  ${share(c.count, people)}`,
  }));
  // Enough room per row to read the label, capped so a twenty-option question does not
  // become a page of its own.
  const height = Math.max(80, Math.min(rows.length * 34 + 24, 460));
  const donut = question.answer_type === "yes_no" && rows.some((r) => r.count > 0);

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
      {/* Said on the page rather than left for the reader to notice: on a multi-select
          the shares of people add past 100%, and a column that does that looks broken
          unless the page says why. */}
      {multi && picks > 0 ? (
        <p className="mt-0.5 text-xs text-muted">{msg.report.picksLine(picks, people)}</p>
      ) : null}

      {donut ? (
        <ChartContainer height={200} className="mt-3">
          <PieChart>
            <Tooltip content={<ChartTooltipContent />} />
            <Pie
              data={rows.filter((r) => r.count > 0)}
              dataKey="count"
              nameKey="label"
              innerRadius={45}
              outerRadius={78}
              // The 2px gap is the card surface showing between segments, which is what
              // stops two adjacent steps of one hue reading as a single block.
              paddingAngle={2}
              stroke="var(--raised)"
              strokeWidth={2}
              isAnimationActive={false}
              label={({ name, value }: { name?: string; value?: number }) =>
                `${name} ${value} (${share(Number(value ?? 0), people)})`
              }
              labelLine={false}
            >
              {rows
                .filter((r) => r.count > 0)
                .map((row, i) => (
                  <Cell key={row.label} fill={i === 0 ? CHART_MARK : "var(--accent)"} />
                ))}
            </Pie>
          </PieChart>
        </ChartContainer>
      ) : rows.length > 0 ? (
        <ChartContainer height={height} className="mt-3">
          {/* Room at the end for the label the bar carries. A multi-select prints two
              percentages rather than one, and the longest bar is the one with no room
              to spare: at 92 the "4 100% · 30.8%" on a full-width bar wrapped onto two
              lines and ran off the plot. */}
          <BarChart
            data={rows}
            layout="vertical"
            margin={{ top: 4, right: multi ? 150 : 92, bottom: 4, left: 4 }}
          >
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="label"
              width={150}
              tickLine={false}
              axisLine={{ stroke: CHART_GRID }}
              tick={{ fill: CHART_AXIS }}
            />
            <Tooltip cursor={{ fill: CHART_GRID }} content={<ChartTooltipContent />} />
            {/* A rating's average, drawn on the scale it belongs to. The number is
                already in the line above; the line is what makes it a position rather
                than a fact to hold in your head while reading the bars. */}
            {question.answer_type === "rating" && question.average !== null ? (
              <ReferenceLine
                x={question.average}
                stroke={CHART_AXIS}
                strokeDasharray="3 3"
                label={{
                  value: msg.report.average(question.average.toFixed(1)),
                  position: "top",
                  fill: CHART_AXIS,
                  fontSize: 11,
                }}
              />
            ) : null}
            <Bar
              dataKey="count"
              fill={CHART_MARK}
              radius={[0, 4, 4, 0]}
              label={{
                position: "right",
                fill: CHART_AXIS,
                fontSize: 12,
                dataKey: "marked",
              }}
              isAnimationActive={false}
            >
              {rows.map((row) => (
                // A write-in is the respondent's own words rather than an option the
                // author offered, so it is drawn in the lighter step of the same hue:
                // still one series, with the distinction carried by the "(write-in)" in
                // the label rather than by colour alone.
                <Cell key={row.label} fill={row.writeIn ? "var(--accent)" : CHART_MARK} />
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
