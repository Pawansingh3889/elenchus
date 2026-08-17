"use client";

import { seriesColour } from "@/lib/comparison";
import { useT } from "@/lib/i18n/useT";
import type { MatrixQuestion } from "@/lib/types";

/**
 * Pick the question whose answers split the room.
 *
 * Beside the slice control and doing the opposite job: slicing narrows the page to one
 * group, comparing keeps everybody and colours them. The two combine, and the order
 * reads correctly either way, because a slice happens first and the groups are formed
 * from whoever survived it.
 *
 * Only questions with a small fixed set of answers are offered. Grouping on a
 * multi-select puts one person in several groups at once and grouping on free text makes
 * a group per respondent; both produce a chart nobody can read, so neither is offered
 * rather than being offered and disappointing.
 */
export function CompareControl({
  questions,
  compareBy,
  onChange,
  groups,
}: {
  questions: MatrixQuestion[];
  compareBy: string | null;
  onChange: (id: string | null) => void;
  groups: string[];
}) {
  const { results } = useT();
  const groupable = questions.filter(
    (q) => q.answer_type === "single_select" || q.answer_type === "yes_no" || q.answer_type === "rating",
  );
  if (groupable.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <label className="flex items-center gap-2 text-sm text-muted">
        {results.compareLabel}
        <select
          className="field w-auto"
          value={compareBy ?? ""}
          onChange={(e) => onChange(e.target.value || null)}
        >
          <option value="">{results.compareNone}</option>
          {groupable.map((q) => (
            <option key={q.id} value={q.id}>
              {q.text}
            </option>
          ))}
        </select>
      </label>

      {/* The legend, once, here rather than repeated on every card below. It is always
          present when there is more than one series, because identity must never be
          carried by colour alone, and the swatches are the same tokens the bars use. */}
      {groups.length > 0 ? (
        <div className="flex flex-wrap items-center gap-3 text-sm">
          {groups.map((label, i) => (
            <span key={label} className="flex items-center gap-1.5">
              <span
                className="size-2.5 shrink-0 rounded-sm"
                style={{ background: seriesColour(i, label) }}
                aria-hidden
              />
              <span className="text-muted">{label}</span>
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
