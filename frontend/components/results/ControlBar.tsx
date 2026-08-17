"use client";

import { X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { seriesColour } from "@/lib/comparison";
import { useT } from "@/lib/i18n/useT";
import { sliceValues, sliceableQuestions, type Slice } from "@/lib/slicing";
import type { MatrixQuestion } from "@/lib/types";

/**
 * Every control that changes what the page shows, in one row that stays on screen.
 *
 * Slice and compare were two rows, each its own component, sitting between the recap and
 * the table. Both scrolled away with it, so by the third question the reader had no way
 * to see what the page was filtered to; and a filtered page that does not say so is how
 * "3 of 4 said yes" gets quoted as the whole survey. This is the pattern every BI tool
 * settled on: the slicers in one band at the top, sticky, with the active state shown as
 * chips beside them so it can be read and cleared without opening a menu.
 *
 * Two controls only. Slicing narrows the page to one group and comparing keeps everybody
 * and colours them; they combine, and the order reads correctly either way because a
 * slice happens first and the groups are formed from whoever survived it. There is no
 * third control, and the guidance that a top bar stops working past four or five is a
 * reason to keep it that way rather than to add a sidebar.
 *
 * Only closed questions are offered by either. Free text cannot be sliced or grouped on:
 * two people describing the same thing in different words are not one group, and a
 * filter that pretends otherwise silently drops half of who it claims to include.
 *
 * Sticky at the top of the viewport rather than under the top bar, because the top bar
 * does not stick: once the page scrolls, this row is the top of it.
 */
export function ControlBar({
  questions,
  slice,
  onSlice,
  compareBy,
  onCompare,
  onClear,
  groups,
  showing,
  total,
}: {
  questions: MatrixQuestion[];
  slice: Slice | null;
  onSlice: (slice: Slice | null) => void;
  compareBy: string | null;
  onCompare: (id: string | null) => void;
  /** Both at once, as one navigation. Calling onSlice(null) then onCompare(null) would
   *  build the second URL from the search params the first had not yet replaced, and
   *  the slice would come straight back. */
  onClear: () => void;
  /** Group labels while comparing, in series order, so the legend lives here once. */
  groups: string[];
  showing: number;
  total: number;
}) {
  const msg = useT();
  const sliceable = sliceableQuestions(questions);
  if (sliceable.length === 0) return null;

  const current = slice ? `${slice.questionId}:${slice.value}` : "all";
  const sliceQuestion = slice ? questions.find((q) => q.id === slice.questionId) : null;
  const compareQuestion = compareBy ? questions.find((q) => q.id === compareBy) : null;
  const anythingSet = Boolean(slice || compareBy);

  return (
    <div className="results-controls sticky top-0 z-10 -mx-4 border-b border-line bg-canvas/95 px-4 py-2 backdrop-blur">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <label className="flex items-center gap-2 text-sm text-muted">
          {msg.results.sliceBy}
          <Select
            value={current}
            onValueChange={(next) => {
              if (next === "all") return onSlice(null);
              const at = next.indexOf(":");
              onSlice({ questionId: next.slice(0, at), value: next.slice(at + 1) });
            }}
          >
            <SelectTrigger className="w-auto min-w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{msg.results.sliceAll}</SelectItem>
              {sliceable.flatMap((question) =>
                // Every value the author wrote, including one nobody picked: an empty
                // group is a finding, and offering only what appears would hide it.
                sliceValues(question).map((value) => (
                  <SelectItem key={`${question.id}:${value}`} value={`${question.id}:${value}`}>
                    {question.text}: {value}
                  </SelectItem>
                )),
              )}
            </SelectContent>
          </Select>
        </label>

        <label className="flex items-center gap-2 text-sm text-muted">
          {msg.results.compareLabel}
          {/* Capped, because a native select sizes itself to its longest option and one
              full question text pushed the whole row onto two lines. The chip below
              carries the full text on hover; here the start of it is enough to choose. */}
          <select
            className="field w-auto max-w-72"
            value={compareBy ?? ""}
            onChange={(e) => onCompare(e.target.value || null)}
          >
            <option value="">{msg.results.compareNone}</option>
            {sliceable.map((q) => (
              <option key={q.id} value={q.id}>
                {q.text}
              </option>
            ))}
          </select>
        </label>

        {/* Live count, always: a reader glancing at the bar should be able to tell
            whether they are looking at everybody without decoding the controls. */}
        <span className="text-sm text-muted tabular-nums">
          {msg.results.sliceShowing(showing, total)}
        </span>
      </div>

      {/* The active state, said again as chips. The selects above already show it, but a
          select shows one line of a long question and no way to remove it in place; a
          chip names the value and carries its own x. Both stay, because the chip is how
          you see and clear, and the select is how you choose. */}
      {anythingSet ? (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {slice && sliceQuestion ? (
            <Badge variant="accent" className="gap-1.5 py-1 pe-1">
              <span className="text-muted">{msg.results.chipOnly}</span>
              <span className="max-w-64 truncate" title={sliceQuestion.text}>
                {sliceQuestion.text}
              </span>
              <span>= {slice.value}</span>
              <button
                type="button"
                className="ms-0.5 rounded-full p-0.5 hover:bg-surface"
                aria-label={msg.results.chipRemove}
                onClick={() => onSlice(null)}
              >
                <X className="size-3" aria-hidden />
              </button>
            </Badge>
          ) : null}

          {compareQuestion ? (
            <Badge variant="neutral" className="gap-1.5 py-1 pe-1">
              <span className="text-muted">{msg.results.chipCompare}</span>
              <span className="max-w-64 truncate" title={compareQuestion.text}>
                {compareQuestion.text}
              </span>
              <button
                type="button"
                className="ms-0.5 rounded-full p-0.5 hover:bg-surface"
                aria-label={msg.results.chipRemove}
                onClick={() => onCompare(null)}
              >
                <X className="size-3" aria-hidden />
              </button>
            </Badge>
          ) : null}

          {/* The legend, once, beside the chip that created it. Always present when
              there is more than one series, because identity must never be carried by
              colour alone, and the swatches are the same tokens the bars use. */}
          {groups.length > 0 && compareBy ? (
            <span className="flex flex-wrap items-center gap-3 text-sm">
              {groups.map((label, i) =>
                // A legend entry is a group, and a group is a slice waiting to happen:
                // clicking one narrows the page to it, the same as clicking its bar
                // would. "other" is a fold of several groups and names no single
                // answer, so it stays a label.
                label === "other" ? (
                  <span key={label} className="flex items-center gap-1.5">
                    <span
                      className="size-2.5 shrink-0 rounded-sm"
                      style={{ background: seriesColour(i, label) }}
                      aria-hidden
                    />
                    <span className="text-muted">{label}</span>
                  </span>
                ) : (
                  <Button
                    key={label}
                    variant="quiet"
                    size="sm"
                    className="gap-1.5 px-1"
                    title={msg.results.legendSlice(label)}
                    onClick={() =>
                      onSlice(
                        slice?.questionId === compareBy && slice.value === label
                          ? null
                          : { questionId: compareBy, value: label },
                      )
                    }
                  >
                    <span
                      className="size-2.5 shrink-0 rounded-sm"
                      style={{ background: seriesColour(i, label) }}
                      aria-hidden
                    />
                    <span className="text-muted">{label}</span>
                  </Button>
                ),
              )}
            </span>
          ) : null}

          <Button variant="quiet" size="sm" onClick={onClear}>
            <X aria-hidden />
            {msg.results.sliceClear}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
