/**
 * How the lens writes its numbers.
 *
 * Unknown is never zero. A figure the provider did not report reads "not reported", a cost
 * nobody priced reads "unpriced", and a sum over attempts some of which reported nothing
 * reads "at least". Each of those is a different fact, and a zero would hide all three.
 */

const numbers = new Intl.NumberFormat("en-GB");

export function milliseconds(value: number | null): string {
  if (value === null) return "not reported";
  if (value >= 10_000) return `${(value / 1000).toFixed(1)} s`;
  return `${numbers.format(Math.round(value))} ms`;
}

export function tokenCount(value: number | null, unmetered = 0): string {
  if (value === null) return "not reported";
  const text = numbers.format(value);
  return unmetered > 0 ? `at least ${text}` : text;
}

export function dollars(value: number | null, unmetered = 0): string {
  if (value === null) return "unpriced";
  // Six places below a cent, four below a dollar: one gpt-5.5 turn cost $0.017095, and two
  // places showed it as $0.02, which is the precision this page exists to keep.
  const places = value < 0.01 ? 6 : value < 1 ? 4 : 2;
  const text = value === 0 ? "$0" : `$${value.toFixed(places)}`;
  return unmetered > 0 ? `at least ${text}` : text;
}

export function moment(iso: string): string {
  return new Date(iso).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });
}

/** The median of what was measured, or null when nothing was. */
export function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

/** A share as a whole percentage, or "no data" when there is nothing to divide by. */
export function percent(part: number, whole: number): string {
  return whole === 0 ? "no data" : `${Math.round((part / whole) * 100)}%`;
}

/** Below this many samples a percentile or a trend is a story, not a measurement. */
export const TOO_FEW = 5;
