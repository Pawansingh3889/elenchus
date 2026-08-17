"use client";

import { useT } from "@/lib/i18n/useT";
import type { Flag } from "@/lib/flags";

/**
 * What to look at first, above the charts it points into.
 *
 * The only status colour on the report, and the reason the series palette stops at four
 * hues instead of taking amber for a fifth: a colour that means "look here" stops meaning
 * it the moment it also means "packing". `lib/flags.ts` holds what may be flagged and,
 * more to the point, what may not.
 *
 * Each line carries an icon and a sentence, so the strip reads the same in greyscale, to
 * a reader who cannot separate the hues, and under forced colours. Nothing here is
 * carried by amber alone; the amber is how it is found on the page, not what it says.
 *
 * Clicking a line moves to the question rather than filtering to it. A flag is a reason
 * to read the chart, and the chart is a hundred pixels below.
 */
export function FlagStrip({ flags }: { flags: Flag[] }) {
  const { report } = useT();
  if (flags.length === 0) return null;

  return (
    // Not `.notice`, which is the same three tokens and the right look. It is an
    // unlayered class rule, so its `align-items: center` beats any utility written here
    // and every line would centre itself against the heading. Utilities all the way down
    // instead, from the same tokens the guard measures.
    <section
      className="flex flex-col gap-2 rounded-lg border border-warn-border bg-warn-fill p-3 text-sm text-warn-text"
      aria-labelledby="flags-heading"
    >
      <h2 id="flags-heading" className="text-sm font-semibold">
        {report.flagsHeading(flags.length)}
      </h2>
      {/* No markers. The `*` reset zeroes padding but leaves `list-style`, so the discs
          rendered on the box's own border rather than inside its padding. */}
      <ul className="flex list-none flex-col gap-1.5">
        {flags.map((flag) => (
          <li key={`${flag.questionId}-${flag.kind}`}>
            <a
              className="flex items-start gap-2 text-start underline-offset-4 hover:underline"
              href={`#question-${flag.questionId}`}
            >
              {/* Decorative: the sentence beside it already says what is wrong, and a
                  screen reader announcing "warning sign" before every line adds nothing
                  the words do not. */}
              <span aria-hidden>&#9888;</span>
              <span>
                <b className="font-semibold">{report.flagQuestion(flag.position + 1)}</b>{" "}
                {flag.text}
                {" - "}
                {flag.kind === "declined"
                  ? report.flagDeclined(flag.count, flag.of)
                  : report.flagLowRating((flag.average ?? 0).toFixed(1), flag.count)}
              </span>
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
