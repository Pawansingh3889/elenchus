import { cn } from "@/lib/utils";

/** A loading placeholder shaped like the thing it stands in for.
 *
 * The app showed a one-line "Loading…" in six places, so a dashboard arrived by
 * popping in from blank. A skeleton that matches the eventual layout keeps the page
 * from jumping when the data lands.
 *
 * The pulse is switched off under prefers-reduced-motion by globals.css, which turns
 * off every animation at the foot of the file. */
export function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      aria-hidden
      className={cn("animate-pulse rounded-md bg-highlight-soft", className)}
      {...props}
    />
  );
}
