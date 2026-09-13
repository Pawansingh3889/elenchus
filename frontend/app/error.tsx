"use client";

import Link from "next/link";
import { useEffect } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { useT } from "@/lib/i18n/useT";

/**
 * The last resort when a render throws.
 *
 * Without this file Next renders its own generic error page and the whole app, top bar
 * included, disappears. What is left here is a page the reader can still navigate out
 * of, with the failure stated rather than a blank screen.
 *
 * `reset` re-renders the segment, which is the right offer for a transient failure and
 * harmless for a permanent one: it fails again and says the same thing.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { errors, common } = useT();
  useEffect(() => {
    // The digest is the only handle on the server-side stack, which is deliberately not
    // sent to the browser. Logging it is what makes a user report traceable at all.
    console.error("unhandled render error", error.digest, error);
  }, [error]);

  return (
    <div className="page narrow">
      <ErrorBanner error={error} />
      <div className="actions">
        <button type="button" className="btn btn-primary" onClick={reset}>
          {errors.retry}
        </button>
        {/* Home, because `/` needs no user and makes no authenticated request, so it is
            the one place a render crash can always land. */}
        <Link className="btn btn-secondary" href="/">
          {common.backHome}
        </Link>
      </div>
    </div>
  );
}
