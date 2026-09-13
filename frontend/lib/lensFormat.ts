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
