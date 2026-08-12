import { cn } from "@/lib/utils";

/**
 * One number with what it means underneath.
 *
 * `of` is the denominator in words, and it is not decoration: the rates on this
 * dashboard are a share of the people a survey was *for*, not of the people who
 * happened to open it, and those two totals differ by a lot on a survey most of the
 * audience has ignored. Printing the denominator is what stops "50%" being read
 * against whichever total the reader assumes.
 *
 * `value` accepts a string so a caller can pass a dash for a rate that does not exist
 * yet. A rate is null rather than 0 when nobody has started, because 0% reads as
 * everyone refusing.
 */
export function Stat({
  value,
  label,
  of,
  className,
}: {
  value: string | number;
  label: string;
  of?: string;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-0.5", className)}>
      <span className="text-xl font-semibold leading-none tabular-nums">{value}</span>
      <span className="text-sm text-ink">{label}</span>
      {of ? <span className="text-xs text-muted">{of}</span> : null}
    </div>
  );
}
