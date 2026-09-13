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

/**
 * The captured call the interpretability pages are reading, kept in the URL beside the
 * filter so the three pages read the same call and a reading can be linked. Changing the
 * survey or run filter drops it, because the call may not be in the new slice.
 */
export function useSelectedAsk(): [string | null, (spanId: string | null) => void] {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const select = useCallback(
    (spanId: string | null) => {
      const query = new URLSearchParams(params.toString());
      if (spanId) query.set("ask", spanId);
      else query.delete("ask");
      const text = query.toString();
      router.replace(text ? `${pathname}?${text}` : pathname, { scroll: false });
    },
    [params, pathname, router],
  );
  return [params.get("ask"), select];
}
