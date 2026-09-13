"use client";

import { ApiError } from "@/lib/api";
import { useT } from "@/lib/i18n/useT";

/**
 * A failure, rendered as the kind of failure it is.
 *
 * A 409 is the server having read the request and declined it, and its message is the
 * reason, which is the useful part; a 503 is an outage, where the message is boilerplate
 * and retrying is the whole advice. Shown identically, a reader could not tell a refusal
 * from a network blip, and the obvious response, clicking again, was wrong.
 *
 * A refusal therefore gets no retry button. That is the point of separating them.
 */
export function ErrorBanner({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const { errors } = useT();
  if (!error) return null;

  const status = error instanceof ApiError ? error.status : 0;
  const message = error instanceof Error ? error.message : String(error);
  const refusal = status === 409;
  const outage = status === 503;
  const title = refusal ? errors.refusedTitle : outage ? errors.outageTitle : errors.genericTitle;

  return (
    <div role="alert" className={refusal ? "error-banner error-banner-refusal" : "error-banner"}>
      <p className="error-banner-title">{title}</p>
      {/* The server's own words. On a refusal this is the checker's reasoning and is the
          only thing worth reading; on an outage it is boilerplate, so the standing advice
          is printed under it rather than instead of it. */}
      <p>{message}</p>
      {outage ? <p>{errors.outageBody}</p> : null}
      {onRetry && !refusal ? (
        <button type="button" className="btn btn-quiet" onClick={onRetry}>
          {errors.retry}
        </button>
      ) : null}
    </div>
  );
}
