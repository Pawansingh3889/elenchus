import { expect, test } from "vitest";

// The guard script itself, imported for its one exported function. Importing it does
// not run the scan: that is behind an entry-point check, so this stays a unit test of
// the extraction rather than a second full pass over the codebase.
import { classNamesIn } from "../scripts/check-tailwind-classes.mjs";

/**
 * The class guard read every form of className except the commonest one.
 *
 * `classNamesIn` collects regions where a class may legitimately appear, then pulls the
 * quoted literals out of each region. For `className={...}`, `cn(...)` and `cva(...)`
 * the region is an expression and still contains its quotes, so the second pass finds
 * them. For `className="..."` the region was the capture group, which is the text
 * *between* the quotes: no quoted literal, nothing collected, class never checked.
 *
 * So the guard was reporting on assembled class lists only. It caught a CSS-less name
 * inside a `cn()` on 17 Aug 2026 while the identical `results-controls` in a plain
 * string had been passing since the day it was written, along with a `qcard-policy` on
 * a builder label that had never had a rule anywhere.
 *
 * This test exists because a guard is the one kind of code that fails silently when it
 * breaks: it goes on exiting 0, and 0 is what it says when it checks nothing at all.
 */
test("a class in a plain className string is collected, not just one inside cn()", () => {
  const source = `
    export function Card() {
      return <div className="rounded-md inset-inline-end-3">
        <span className={cn("p-2", flag && "text-warn-text")} />
      </div>;
    }
  `;

  const found = classNamesIn(source);

  // The plain string: the case that was invisible. `inset-inline-end-3` is the real
  // invented utility this guard was written for, so it is the one used here.
  expect(found.has("rounded-md")).toBe(true);
  expect(found.has("inset-inline-end-3")).toBe(true);

  // The forms that always worked, kept so a fix to one cannot quietly drop the other.
  expect(found.has("p-2")).toBe(true);
  expect(found.has("text-warn-text")).toBe(true);
});

/**
 * The narrowing that keeps the guard usable is part of what it does, so it is pinned
 * here too: reading every literal in a file turned up import specifiers and query keys,
 * and the noise buried the findings this exists to surface.
 */
test("a string outside a class position is not collected", () => {
  const found = classNamesIn(`
    const key = "survey-template-list";
    useQuery({ queryKey: ["answers-by-run"] });
    return <div className="flex gap-2" />;
  `);

  expect(found.has("flex")).toBe(true);
  expect(found.has("gap-2")).toBe(true);
  expect(found.has("survey-template-list")).toBe(false);
  expect(found.has("answers-by-run")).toBe(false);
});
