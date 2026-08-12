import { Skeleton } from "@/components/ui/skeleton";

/** Shaped like the dashboard it stands in for, so the page does not jump when the data
 *  lands. The app showed a one-line "Loading…" here and arrived by popping in. */
export default function Loading() {
  return (
    <div className="flex flex-col gap-4 p-4">
      <Skeleton className="h-10 w-full max-w-2xl" />
      <Skeleton className="h-24 w-full" />
      <div className="flex flex-col gap-2">
        {[0, 1, 2].map((row) => (
          <Skeleton key={row} className="h-20 w-full" />
        ))}
      </div>
    </div>
  );
}
