"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { api } from "./api";
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
