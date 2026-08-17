"use client";

import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
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
import { Button } from "@/components/ui/button";
import { Card, CardLabel } from "@/components/ui/card";
import { seriesColour } from "@/lib/comparison";
import { useT } from "@/lib/i18n/useT";
import { SLICEABLE_TYPES, type Slice } from "@/lib/slicing";
import type { QuestionReport } from "@/lib/types";

/**
 * More rows than this is a long list. One number, two consequences: the card goes full
 * width so its labels get an axis they fit on, and its zero rows fold behind a count.
 * Eight because it is the largest option list that still reads as a glance at half
 * width, and because the plant's own surveys sit either side of it: an area list of
 * eight, a location list of eleven.
 */
export const LONG_LIST = 8;

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
 *
 * **A mark is a filter.** Clicking a bar or a donut segment slices the page to the
 * people who gave that answer, and clicking it again clears the slice: the same
 * `?slice=` the control bar sets, reached from the chart instead of the menu. This is
 * the interaction every BI tool is built around, and it costs almost nothing here
 * because slicing already existed; what it adds is that "did the people who said X also
 * say Y" is one click on X rather than a hunt through a select. Write-ins are not
 * clickable, for the reason `lib/slicing.ts` gives: one person's words are not a group.
 * The keyboard path stays the control bar, since an SVG rectangle is not focusable.
 */
export function QuestionCard({
  question,
  position,
  series = [],
  flagged = false,
  slice = null,
  onSlice,
  pageComparing = false,
  children,
}: {
  question: QuestionReport;
  position: number;
  /** One tally per compared group. Empty when nothing is being compared, which is the
   *  ordinary case and the one that stays a single series. */
  series?: { label: string; report: QuestionReport }[];
  /** Named in the strip at the top of the page, so the card says so on arrival. */
  flagged?: boolean;
  /** The page's current slice, so a mark on this card can show it is the one selected. */
  slice?: Slice | null;
  /** Set or clear the slice from a mark. Absent means marks are not clickable. */
  onSlice?: (slice: Slice | null) => void;
  /** Whether the page is comparing at all, so the compared question, which draws one
   *  series, still takes the full width its neighbours do. */
  pageComparing?: boolean;
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

  // Which marks act. Only the types the slicer accepts, and only when the page gave us
  // a way to set it: the same rule in one place, so a card can never offer a click the
  // control bar could not have made.
  const clickable =
    Boolean(onSlice) && (SLICEABLE_TYPES as readonly string[]).includes(question.answer_type);
  const selectedHere = slice && slice.questionId === question.id ? slice.value : null;
  const toggle = (value: string, writeIn: boolean) => {
    if (!clickable || writeIn || !onSlice) return;
    onSlice(selectedHere === value ? null : { questionId: question.id, value });
  };
  // Recharts hands a click the drawn item, and the row it was drawn from sits on its
  // `payload`; the same shape for a bar rectangle and a pie sector, which is why one
  // handler serves both.
  const onMark = (item: { payload?: Record<string, unknown> }) => {
    const row = item.payload ?? {};
    toggle(String(row.value ?? ""), Boolean(row.writeIn));
  };
  // Said in the tooltip, because a mark that acts has to say so somewhere and the
  // tooltip is what the reader is looking at when they are about to click.
  const hint = (row: Record<string, unknown>): string | null => {
    if (!clickable || row.writeIn) return null;
    if (selectedHere === row.value) return msg.results.clickToUnslice;
    return msg.results.clickToSlice(Number(row.count ?? 0));
  };
  // Selected state: the chosen mark keeps its colour and the rest of this card's marks
  // step back. Only on the card the slice is on; every other card is showing the group
  // and has nothing to dim. Opacity rather than a second hue, so the mark stays the same
  // colour it was, only quieter, and its count still prints in full.
  const dimmed = (value: string) => selectedHere !== null && selectedHere !== value;

  // Comparing turns one bar per option into one bar per option per group, which is the
  // only arrangement on this page where colour identifies anything. The whole-survey
  // tally still supplies the option order, so the rows do not reshuffle when a
  // comparison is turned on.
  const comparing = series.length > 1;
  const grouped = comparing
    ? question.counts.map((c) => {
        const row: Record<string, string | number | boolean> = {
          label: c.write_in ? `${c.label} ${msg.report.writeIn}` : c.label,
          value: c.label,
          writeIn: c.write_in,
        };
        for (const s of series) {
          row[s.label] = s.report.counts.find((x) => x.label === c.label)?.count ?? 0;
        }
        return row;
      })
    : [];

  const rows = question.counts.map((c) => ({
    label: c.write_in ? `${c.label} ${msg.report.writeIn}` : c.label,
    // The undecorated option, which is what a slice is keyed on.
    value: c.label,
    count: c.count,
    writeIn: c.write_in,
    // The label printed at the end of the mark: the count, then its share of people,
    // then on a multi-select its share of the picks as well.
    marked: multi
      ? `${c.count}  ${share(c.count, people)} · ${share(c.count, picks)}`
      : `${c.count}  ${share(c.count, people)}`,
  }));
  // A long list is a different kind of card, decided by one number, with two
  // consequences that belong together. It goes full width, so its labels get an axis
  // they fit on: at 150px, "Chilled finished goods store" wrapped and still ran four
  // pixels past the plot. And its zero rows fold, because thirteen rows for a question
  // five people answered is mostly a column of empty space, and eight zeros are a
  // finding a reader can be told in one line rather than shown in eight. Rating never
  // folds: its five steps are the scale, and an unused end of it is the shape.
  //
  // Comparing also goes wide regardless, since one bar per option per group needs the
  // room, and any card is short of it at half width.
  const longList = rows.length > LONG_LIST && question.answer_type !== "rating";
  // Wide when this card compares, when the page does (the compared question itself
  // draws one series, and left at half width it sat alone beside a column of wide
  // cards), or when its list is long. Free text has no chart and never needs the room.
  const wide = (comparing || pageComparing || longList) && rows.length > 0;
  // 240 fits the longest option this plant has written so far ("Slightly worse than
  // last summer", 224px at the tick size) with room; 150 is what a six-option scale
  // wraps comfortably into at half width.
  const axisWidth = wide ? 240 : 150;
  const [unfolded, setUnfolded] = useState(false);
  const zeroRows = longList ? rows.filter((r) => r.count === 0).length : 0;
  const folded = longList && !unfolded && zeroRows > 0;
  const shownRows = folded ? rows.filter((r) => r.count > 0) : rows;
  const shownGrouped = folded
    ? grouped.filter((row) => series.some((s) => Number(row[s.label]) > 0))
    : grouped;
  // Enough room per row to read the label, capped so a twenty-option question does not
  // become a page of its own.
  const height = Math.max(80, Math.min(shownRows.length * 34 + 24, 460));
  // A donut is two parts of one whole, which is exactly what a yes/no is until you
  // compare groups: then it is two wholes, and a donut can only draw one. Comparing
  // therefore wins, and the same question answers "how split" and "who differs"
  // depending on what was asked of it.
  const donut = question.answer_type === "yes_no" && !comparing && rows.some((r) => r.count > 0);
  const chartClass = clickable
    ? "mt-3 [&_.recharts-bar-rectangle]:cursor-pointer [&_.recharts-pie-sector]:cursor-pointer"
    : "mt-3";

  return (
    // The anchor the flag strip links to, and a scroll margin so the card lands below
    // the sticky control bar rather than under it. The span is the card's own decision
    // because it depends on the data the card holds; the grid it sits in stays dumb.
    <Card
      id={`question-${question.id}`}
      className={wide ? "scroll-mt-28 p-4 lg:col-span-2" : "scroll-mt-28 p-4"}
    >
      <div className="flex flex-wrap items-center gap-2">
        <CardLabel>{msg.builder.questionLabel(position + 1)}</CardLabel>
        {/* The same words the strip used, so arriving here confirms the jump landed
            where it said it would. Icon and text, never the amber alone. */}
        {flagged ? (
          <span className="rounded-md border border-warn-border bg-warn-fill px-1.5 py-0.5 text-xs text-warn-text">
            <span aria-hidden>&#9888;</span> {msg.report.flagged}
          </span>
        ) : null}
      </div>
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
        <ChartContainer height={200} className={chartClass}>
          <PieChart>
            <Tooltip content={<ChartTooltipContent hint={hint} />} />
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
              onClick={onMark}
            >
              {rows
                .filter((r) => r.count > 0)
                .map((row, i) => (
                  <Cell
                    key={row.label}
                    fill={i === 0 ? CHART_MARK : "var(--accent)"}
                    fillOpacity={dimmed(row.value) ? 0.35 : 1}
                  />
                ))}
            </Pie>
          </PieChart>
        </ChartContainer>
      ) : comparing && grouped.length > 0 ? (
        <ChartContainer height={Math.max(120, shownGrouped.length * (series.length * 16 + 18) + 24)} className={chartClass}>
          <BarChart data={shownGrouped} layout="vertical" margin={{ top: 4, right: 40, bottom: 4, left: 4 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="label"
              width={axisWidth}
              tickLine={false}
              axisLine={{ stroke: CHART_GRID }}
              tick={{ fill: CHART_AXIS }}
            />
            <Tooltip cursor={{ fill: CHART_GRID }} content={<ChartTooltipContent hint={hint} />} />
            {series.map((s, i) => (
              <Bar
                key={s.label}
                dataKey={s.label}
                fill={seriesColour(i, s.label)}
                radius={[0, 4, 4, 0]}
                // The count on every bar, so the chart reads in greyscale and to anyone
                // who cannot separate the hues. The legend lives once above the cards
                // rather than on each of them.
                label={{ position: "right", fill: CHART_AXIS, fontSize: 11 }}
                isAnimationActive={false}
                onClick={onMark}
              >
                {shownGrouped.map((row) => (
                  <Cell
                    key={String(row.value)}
                    fillOpacity={dimmed(String(row.value)) ? 0.35 : 1}
                  />
                ))}
              </Bar>
            ))}
          </BarChart>
        </ChartContainer>
      ) : shownRows.length > 0 ? (
        <ChartContainer height={height} className={chartClass}>
          {/* Room at the end for the label the bar carries. A multi-select prints two
              percentages rather than one, and the longest bar is the one with no room
              to spare: at 92 the "4 100% · 30.8%" on a full-width bar wrapped onto two
              lines and ran off the plot. */}
          <BarChart
            data={shownRows}
            layout="vertical"
            margin={{ top: 4, right: multi ? 150 : 92, bottom: 4, left: 4 }}
          >
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="label"
              width={axisWidth}
              tickLine={false}
              axisLine={{ stroke: CHART_GRID }}
              tick={{ fill: CHART_AXIS }}
            />
            <Tooltip cursor={{ fill: CHART_GRID }} content={<ChartTooltipContent hint={hint} />} />
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
              onClick={onMark}
            >
              {shownRows.map((row) => (
                // A write-in is the respondent's own words rather than an option the
                // author offered, so it is drawn in the lighter step of the same hue:
                // still one series, with the distinction carried by the "(write-in)" in
                // the label rather than by colour alone.
                <Cell
                  key={row.label}
                  fill={row.writeIn ? "var(--accent)" : CHART_MARK}
                  fillOpacity={dimmed(row.value) ? 0.35 : 1}
                />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      ) : null}

      {/* The zeros, said rather than drawn. The count is the finding ("eight of the
          eleven places were never named"), and it stays on the card whether folded or
          not; unfolding draws the rows for a reader who wants to see which. Once
          unfolded it stays unfolded for this card, so a slice does not snap it shut. */}
      {longList && zeroRows > 0 ? (
        <Button
          variant="quiet"
          size="sm"
          className="mt-2 -ms-2 text-muted"
          aria-expanded={unfolded}
          onClick={() => setUnfolded((v) => !v)}
        >
          {unfolded ? <ChevronDown aria-hidden /> : <ChevronRight aria-hidden />}
          {unfolded ? msg.results.foldZeros(zeroRows) : msg.results.unfoldZeros(zeroRows)}
        </Button>
      ) : null}

      {children}

      {question.answered === 0 && question.declined === 0 ? (
        <p className="mt-2 text-sm text-muted">{msg.report.noAnswers}</p>
      ) : null}
    </Card>
  );
}
