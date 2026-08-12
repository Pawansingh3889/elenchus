import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import * as React from "react";
import { beforeEach, expect, test, vi } from "vitest";

import { api } from "@/lib/api";
import {
  useDeleteTemplate,
  usePublishTemplate,
  useSummariseSurvey,
} from "@/lib/queries";
import { useUserStore } from "@/lib/store";
import type { SurveyRecapStatus, SurveySummary } from "@/lib/types";

/**
 * The cache keys these mutations touch, because two of them were wrong.
 *
 * Every template mutation invalidated `["templates"]`, a key with no query behind it:
 * the Build list page it belonged to had been deleted and the invalidations outlived
 * it. Only closing a survey also invalidated `["dashboard"]`. So publishing and then
 * going home showed the old status, and deleting a template, which navigates home on
 * success, landed the author on a dashboard still listing the survey they had just
 * deleted.
 *
 * The recap had the mirror-image fault: it wrote to `["survey-recap", …]` and nothing
 * read that key, so the write was dead and the recap survived only in mutation state.
 * Leaving the tab and coming back lost it, and the author paid another model call to
 * read prose the column already held.
 */

const AUTHOR = "00000000-0000-0000-0000-0000000000a1";

function wrapper(client: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

beforeEach(() => {
  useUserStore.setState({ currentUserId: AUTHOR });
  vi.restoreAllMocks();
});

test("deleting a template invalidates the dashboard it navigates back to", async () => {
  vi.spyOn(api, "deleteTemplate").mockResolvedValue(undefined);
  const client = new QueryClient();
  const invalidated = vi.spyOn(client, "invalidateQueries");

  const { result } = renderHook(() => useDeleteTemplate("t1"), { wrapper: wrapper(client) });
  result.current.mutate();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));

  const keys = invalidated.mock.calls.map((call) => call[0]?.queryKey?.[0]);
  expect(keys).toContain("dashboard");
  // The key that had no query behind it. Naming it here so a re-added invalidation
  // has to explain itself rather than passing unnoticed.
  expect(keys).not.toContain("templates");
});

test("publishing invalidates the dashboard and what a respondent can open", async () => {
  vi.spyOn(api, "publishTemplate").mockResolvedValue({
    id: "v1",
    template_id: "t1",
    version: 1,
    published_at: "2026-08-12T00:00:00Z",
  });
  const client = new QueryClient();
  const invalidated = vi.spyOn(client, "invalidateQueries");

  const { result } = renderHook(() => usePublishTemplate("t1"), { wrapper: wrapper(client) });
  result.current.mutate();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));

  const keys = invalidated.mock.calls.map((call) => call[0]?.queryKey?.[0]);
  expect(keys).toContain("dashboard");
  expect(keys).toContain("template");
  expect(keys).toContain("published-surveys");
});

test("a generated recap lands on the key the page reads", async () => {
  const summary: SurveySummary = {
    headline: "The line stops most often at the guillotine.",
    findings: [],
    notable_quotes: [],
    version: 1,
    runs_included: 3,
    generated_at: "2026-08-12T00:00:00Z",
  };
  vi.spyOn(api, "summariseSurvey").mockResolvedValue(summary);
  const client = new QueryClient();

  const { result } = renderHook(() => useSummariseSurvey("t1"), { wrapper: wrapper(client) });
  result.current.mutate(false);
  await waitFor(() => expect(result.current.isSuccess).toBe(true));

  // The same key and the same envelope shape useSurveyRecap reads, so the recap
  // survives a navigation instead of costing a second model call.
  const cached = client.getQueryData<SurveyRecapStatus>(["survey-recap", "t1", AUTHOR]);
  expect(cached?.recap?.headline).toBe(summary.headline);
  expect(cached?.absence).toBeNull();
});
