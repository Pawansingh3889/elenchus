"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { api, ApiError } from "./api";
import type { LensScope } from "./lensScope";
import { useUserStore } from "./store";

export function useUsers() {
  const userId = useUserStore((s) => s.currentUserId);
  // Not fetched until somebody is acting, because without an id this request cannot
  // succeed: the endpoint requires a caller and the browser has none to send. Firing it
  // anyway meant every cold load spent a request to be told 401 and logged a console
  // error for it, which is a real failure sitting in the overlay on a page that is
  // working exactly as intended.
  return useQuery({ queryKey: ["users"], queryFn: api.listUsers, enabled: !!userId });
}

/** Whether a provider session exists, and whose.
 *
 * The cookie a real sign-in sets is HttpOnly, so the browser cannot read it and cannot
 * tell a signed-in visitor from a signed-out one without asking. This asks, once, and
 * writes the id into the store on the way through: everything else in the app already
 * reads that store, and the API client still sends the header from it, so one answer
 * serves both sign-in methods rather than each page learning about both.
 */
export function useSession() {
  const setCurrentUserId = useUserStore((s) => s.setCurrentUserId);
  const query = useQuery({
    queryKey: ["session"],
    queryFn: api.session,
    staleTime: 5 * 60 * 1000,
    // A signed-out visitor is an answer, not an outage: retrying it four times on every
    // page load is noise in the console and load on the API.
    retry: false,
  });
  useEffect(() => {
    if (query.data) {
      setCurrentUserId(query.data.id);
    } else if (query.isFetched && !query.data) {
      setCurrentUserId(null);
    }
  }, [query.data, query.isFetched, setCurrentUserId]);
  return query;
}

/** Which real sign-in providers exist, so the top bar draws only buttons that work.
 *  Asked once and cached: the answer is a property of the deployment, not of the user. */
export function useProviders() {
  return useQuery({
    queryKey: ["providers"],
    queryFn: () => api.providers(),
    staleTime: Infinity,
  });
}

/** Sign in, for the development shim. Stores the id and refetches the picker, which was
 *  empty until this moment precisely because there was no id to fetch it with. */
export function useIdentify() {
  const qc = useQueryClient();
  const setCurrentUserId = useUserStore((s) => s.setCurrentUserId);
  return useMutation({
    mutationFn: (email: string) => api.identify(email),
    onSuccess: (user) => {
      setCurrentUserId(user.id);
      void qc.invalidateQueries();
    },
  });
}

export function usePublishedSurveys() {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["published-surveys", userId],
    queryFn: api.listPublished,
    enabled: !!userId,
  });
}

export function useRun(id: string) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["run", id, userId],
    queryFn: () => api.getRun(id),
    enabled: !!userId,
  });
}

export function useStartRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (templateId: string) => api.startRun(templateId),
    // The run just created belongs in the resumable list, and the published list now
    // carries whether this person has answered. Neither was invalidated, so a second
    // click within one session saw a stale page and started a second run: the client
    // half of the duplicate-response bug the engine now refuses.
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["my-runs"] });
      qc.invalidateQueries({ queryKey: ["published-surveys"] });
    },
  });
}

/** The respondent's own unfinished runs, so the home can offer Continue. */
export function useMyUnfinishedRuns() {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["my-runs", userId],
    queryFn: api.myUnfinishedRuns,
    enabled: !!userId,
  });
}

export function useSendRunMessage(id: string) {
  const qc = useQueryClient();
  const userId = useUserStore((s) => s.currentUserId);
  return useMutation({
    mutationFn: (content: string) => api.sendRunMessage(id, content),
    // The turn returns the whole updated run, so seed the cache rather than refetch it.
    onSuccess: (run) => qc.setQueryData(["run", id, userId], run),
  });
}

/** Take back the previous answer so it can be given again. Returns the rewound run, in
 *  the same shape a turn does, so it seeds the cache the same way. */
export function useRewindRun(id: string) {
  const qc = useQueryClient();
  const userId = useUserStore((s) => s.currentUserId);
  return useMutation({
    mutationFn: () => api.rewindRun(id),
    onSuccess: (run) => qc.setQueryData(["run", id, userId], run),
  });
}

/** Withdraw a run and everything in it, at the respondent's own request.
 *
 *  The cached run is removed rather than invalidated: invalidating would refetch a run
 *  the server has just erased, and the respondent would watch their withdrawal turn into
 *  a 404 on the page they are still looking at. The unfinished-runs list is invalidated
 *  because the erased run may have been on it. */
export function useDeleteRun(id: string) {
  const qc = useQueryClient();
  const userId = useUserStore((s) => s.currentUserId);
  return useMutation({
    mutationFn: () => api.deleteRun(id),
    onSuccess: () => {
      qc.removeQueries({ queryKey: ["run", id, userId] });
      void qc.invalidateQueries({ queryKey: ["my-runs"] });
    },
  });
}

/** Reset the demo: wipe all data and re-seed. */
export function useResetDemo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.resetDemo(),
    onSuccess: () => {
      void qc.invalidateQueries();
    },
  });
}

/** The caller as the server sees them. Half of `is_admin` is an email allowlist in
 *  server settings, so the browser cannot work it out and has to ask. */
export function useMe() {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({ queryKey: ["me", userId], queryFn: api.me, enabled: !!userId });
}

/* The lens reads. Keyed by the acting user as well, so switching user in the dev picker
 * never serves one person's view of the trace to another; `enabled` keeps them off the
 * wire until the caller is known to be an administrator. */

export function useLensStrip(enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({ queryKey: ["lens", "strip", userId], queryFn: api.lensStrip, enabled });
}

export function useLensRuns(enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({ queryKey: ["lens", "runs", userId], queryFn: api.lensRuns, enabled });
}

export function useLensSpans(runId: string, enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "spans", runId, userId],
    queryFn: () => api.lensSpans(runId),
    enabled,
  });
}

export function useLensAttempts(scope: LensScope, enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "attempts", scope.surveyId, scope.runId, userId],
    queryFn: () => api.lensAttempts(scope),
    enabled,
    // Refetch keeps the frame: a new filter holds the previous render rather than
    // flashing empty while the next slice loads.
    placeholderData: (previous) => previous,
  });
}

export function useLensDecisions(scope: LensScope, enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "decisions", scope.surveyId, scope.runId, userId],
    queryFn: () => api.lensDecisions(scope),
    enabled,
    placeholderData: (previous) => previous,
  });
}

export function useLensCorrelations(scope: LensScope, enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "correlations", scope.surveyId, scope.runId, userId],
    queryFn: () => api.lensCorrelations(scope),
    enabled,
    placeholderData: (previous) => previous,
  });
}

/* The embedding reads are per survey and may spend money on first view, so they wait for
 * a survey to be chosen and are not retried: a 503 means embeddings are switched off, and
 * asking three more times changes nothing. */

function surveyOf(surveyId: string | null): string {
  if (surveyId === null) throw new Error("An embedding report needs a survey chosen.");
  return surveyId;
}

export function useLensAnswerMap(surveyId: string | null, enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "embeddings", "map", surveyId, userId],
    queryFn: () => api.lensAnswerMap(surveyOf(surveyId)),
    enabled: enabled && surveyId !== null,
    retry: false,
  });
}

export function useLensThemes(surveyId: string | null, enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "embeddings", "themes", surveyId, userId],
    queryFn: () => api.lensThemes(surveyOf(surveyId)),
    enabled: enabled && surveyId !== null,
    retry: false,
  });
}

export function useLensDuplicates(surveyId: string | null, enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "embeddings", "duplicates", surveyId, userId],
    queryFn: () => api.lensDuplicates(surveyOf(surveyId)),
    enabled: enabled && surveyId !== null,
    retry: false,
  });
}

export function useLensGrounding(enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "embeddings", "grounding", userId],
    queryFn: api.lensGrounding,
    enabled,
    retry: false,
  });
}

/* The interpretability reads. An analysis runs a local model for minutes on a CPU, so it
 * is never started by a read: only the Analyse mutation starts one, and a call that has not
 * been analysed reads as null rather than as an error. */

export function useInterpStatus(enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "interp", "status", userId],
    queryFn: api.lensInterpStatus,
    enabled,
    retry: false,
  });
}

export function useInterpAsks(scope: LensScope, enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "interp", "asks", scope.surveyId, scope.runId, userId],
    queryFn: () => api.lensInterpAsks(scope),
    enabled,
    placeholderData: (previous) => previous,
  });
}

export function useInterpAnalysis(spanId: string | null, enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "interp", "analysis", spanId, userId],
    queryFn: async () => {
      if (spanId === null) throw new Error("An analysis needs a call chosen.");
      try {
        return await api.lensInterpAnalysis(spanId);
      } catch (error) {
        // Not analysed yet is a state of the call, and the page offers to start one.
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
    enabled: enabled && spanId !== null,
    retry: false,
  });
}

export function useAnalyse() {
  const qc = useQueryClient();
  const userId = useUserStore((s) => s.currentUserId);
  return useMutation({
    mutationFn: (spanId: string) => api.lensInterpAnalyse(spanId),
    onSuccess: (stored) => {
      qc.setQueryData(["lens", "interp", "analysis", stored.span_id, userId], stored);
      void qc.invalidateQueries({ queryKey: ["lens", "interp", "asks"] });
    },
  });
}

export function useAttribute() {
  const qc = useQueryClient();
  const userId = useUserStore((s) => s.currentUserId);
  return useMutation({
    mutationFn: (spanId: string) => api.lensInterpAttribute(spanId),
    onSuccess: (stored) => {
      qc.setQueryData(["lens", "interp", "analysis", stored.span_id, userId], stored);
      void qc.invalidateQueries({ queryKey: ["lens", "interp", "asks"] });
    },
  });
}

/* The evaluation reads. Labelling changes every rate on the page, so a label refreshes the
 * whole evaluation lens rather than patching one row. */

export function useEvalItems(source: "corpus" | "runs", unlabelled: boolean, enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "evaluation", "items", source, unlabelled, userId],
    queryFn: () => api.lensEvalItems(source, unlabelled),
    enabled,
    placeholderData: (previous) => previous,
  });
}

export function useFaithfulness(enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "evaluation", "faithfulness", userId],
    queryFn: api.lensEvalFaithfulness,
    enabled,
  });
}

export function useQuality(enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["lens", "evaluation", "quality", userId],
    queryFn: api.lensEvalQuality,
    enabled,
  });
}

export function useLabel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      key,
      verdict,
      note,
    }: {
      key: string;
      verdict: "supported" | "invented" | "unsure";
      note: string | null;
    }) => api.lensEvalLabel(key, verdict, note),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["lens", "evaluation"] }),
  });
}

export function useJudgeRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (runId: string) => api.lensEvalJudgeRun(runId),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["lens", "evaluation"] }),
  });
}

export function usePromptFamily(enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({ queryKey: ["prompts", "conduct", userId], queryFn: api.promptFamily, enabled });
}

export function usePromptBody(name: string | null, enabled: boolean) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["prompts", "conduct", "body", name, userId],
    queryFn: () => api.promptBody(name as string),
    enabled: enabled && name !== null,
  });
}

/* Both prompt writes return the whole family, so they seed its cache instead of refetching,
 * and they invalidate the lens: which version is live changes what every page reads next. */

export function useSavePrompt() {
  const qc = useQueryClient();
  const userId = useUserStore((s) => s.currentUserId);
  return useMutation({
    mutationFn: ({ body, note }: { body: string; note: string | null }) => api.savePrompt(body, note),
    onSuccess: (family) => qc.setQueryData(["prompts", "conduct", userId], family),
  });
}

export function useActivatePrompt() {
  const qc = useQueryClient();
  const userId = useUserStore((s) => s.currentUserId);
  return useMutation({
    mutationFn: (name: string) => api.activatePrompt(name),
    onSuccess: (family) => {
      qc.setQueryData(["prompts", "conduct", userId], family);
      void qc.invalidateQueries({ queryKey: ["lens"] });
    },
  });
}
