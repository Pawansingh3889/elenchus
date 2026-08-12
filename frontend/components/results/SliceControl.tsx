"use client";

import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useT } from "@/lib/i18n/useT";
import { sliceValues, sliceableQuestions, type Slice } from "@/lib/slicing";
import type { MatrixQuestion } from "@/lib/types";

/**
 * Read the whole page as one group of respondents rather than as everybody.
 *
 * One control, because a slice is one question and one of its answers. Stacking filters
 * would let an author narrow to a single person without noticing, and the group sizes
 * here are small enough that the second filter is usually the one that does it.
 *
 * Only closed questions are offered. Free text cannot be sliced on: two people
 * describing the same thing in different words are not one group, and a filter that
 * pretends otherwise silently drops half of who it claims to include.
 */
export function SliceControl({
  questions,
  slice,
  onChange,
  showing,
  total,
}: {
  questions: MatrixQuestion[];
  slice: Slice | null;
  onChange: (slice: Slice | null) => void;
  showing: number;
  total: number;
}) {
  const msg = useT();
  const sliceable = sliceableQuestions(questions);
  if (sliceable.length === 0) return null;

  const current = slice ? `${slice.questionId}:${slice.value}` : "all";

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-muted">{msg.results.sliceBy}</span>
      <Select
        value={current}
        onValueChange={(next) => {
          if (next === "all") return onChange(null);
          const at = next.indexOf(":");
          onChange({ questionId: next.slice(0, at), value: next.slice(at + 1) });
        }}
      >
        <SelectTrigger className="w-auto min-w-56">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">{msg.results.sliceAll}</SelectItem>
          {sliceable.flatMap((question) =>
            // Every value the author wrote, including one nobody picked: an empty group
            // is a finding, and offering only what appears in the data would hide it.
            sliceValues(question).map((value) => (
              <SelectItem key={`${question.id}:${value}`} value={`${question.id}:${value}`}>
                {question.text}: {value}
              </SelectItem>
            )),
          )}
        </SelectContent>
      </Select>

      {slice ? (
        <>
          <span className="text-sm text-muted tabular-nums">
            {msg.results.sliceShowing(showing, total)}
          </span>
          <Button variant="quiet" size="sm" onClick={() => onChange(null)}>
            <X aria-hidden />
            {msg.results.sliceClear}
          </Button>
        </>
      ) : null}
    </div>
  );
}
