"use client";

import { AlertTriangle, CloudOff, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import { useT } from "@/lib/i18n/useT";
import { cn } from "@/lib/utils";

/**
 * A failure, rendered as the kind of failure it is.
 *
 * The app rendered every error the same way, as `{(error as Error).message}` in a red
 * line, copied into about fifteen places. That flattened a distinction the backend
 * works hard to make. A 409 is the server having read the request and declined it, and
 * its message is the reason, which is the useful part; a 503 is an outage, where the
 * message is boilerplate and retrying is the whole advice. Shown identically, an author
 * reading "the recap did not hold up against the numbers" was offered no way to tell it
 * from a network blip, and the obvious response, clicking again, was wrong.
 *
 * A refusal therefore gets no retry button. That is the point of separating them.
 */
export function ErrorBanner({
  error,
  onRetry,
  className,
}: {
  error: unknown;
  onRetry?: () => void;
  className?: string;
}) {
  const { errors } = useT();
  if (!error) return null;

  const status = error instanceof ApiError ? error.status : 0;
  const message = error instanceof Error ? error.message : String(error);
  const refusal = status === 409;
  const outage = status === 503;

  const Icon = refusal ? AlertTriangle : outage ? CloudOff : XCircle;
  const title = refusal
    ? errors.refusedTitle
    : outage
      ? errors.outageTitle
      : errors.genericTitle;

  return (
    <div
      role="alert"
      className={cn(
        "flex gap-3 rounded-lg border p-3 text-sm",
        refusal
          ? "bg-warn-fill text-warn-text border-warn-border"
          : "bg-err-fill text-err-text border-err-border",
        className,
      )}
    >
      <Icon className="size-4 shrink-0 mt-0.5" aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="font-medium">{title}</p>
        {/* The server's own words. On a refusal this is the checker's reasoning and is
            the only thing worth reading; on an outage it is boilerplate, so the
            standing advice is printed under it rather than instead of it. */}
        <p className="mt-0.5 break-words">{message}</p>
        {outage ? <p className="mt-0.5">{errors.outageBody}</p> : null}
        {onRetry && !refusal ? (
          <Button variant="quiet" size="sm" className="mt-2 -ms-3" onClick={onRetry}>
            {errors.retry}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
