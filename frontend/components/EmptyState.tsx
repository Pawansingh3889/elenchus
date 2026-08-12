import * as React from "react";

import { cn } from "@/lib/utils";

/** Nothing here, and what to do about it.
 *
 *  `action` matters more than the wording: an empty results page whose answer is "go
 *  and ask people to answer it" should carry the way to do that, not just say so. */
export function EmptyState({
  title,
  body,
  action,
  className,
}: {
  title: string;
  body?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-2 rounded-lg border border-dashed border-line",
        "bg-surface px-6 py-10 text-center",
        className,
      )}
    >
      <p className="text-md font-medium text-ink">{title}</p>
      {body ? <p className="max-w-prose text-sm text-muted">{body}</p> : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}
