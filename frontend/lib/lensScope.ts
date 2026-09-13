"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

/** Which traced runs a factor page is about: all of them, one survey's, or one run. */
export type LensScope = { surveyId: string | null; runId: string | null };

/**
 * The filter lives in the URL rather than in component state, so a narrowed page can be
 * reloaded, linked and compared in two tabs, and every chart below the filter row reads
 * the same slice.
 */
export function useLensScope(): [LensScope, (next: LensScope) => void] {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const scope: LensScope = { surveyId: params.get("survey"), runId: params.get("run") };
  const setScope = useCallback(
    (next: LensScope) => {
      const query = new URLSearchParams();
      if (next.surveyId) query.set("survey", next.surveyId);
      if (next.runId) query.set("run", next.runId);
      const text = query.toString();
      router.replace(text ? `${pathname}?${text}` : pathname, { scroll: false });
    },
    [pathname, router],
  );
  return [scope, setScope];
}
