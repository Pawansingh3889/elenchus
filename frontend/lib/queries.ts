"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./api";
import { useUserStore } from "./store";
import type { RunDetail, SurveyAudience, SurveyRecapStatus, TemplateWrite } from "./types";

export function useUsers() {
  return useQuery({ queryKey: ["users"], queryFn: api.listUsers });
}

/** The acting user's record (id + role), for role-gating nav and pages. */
export function useCurrentUser() {
  const { data: users } = useUsers();
  const userId = useUserStore((s) => s.currentUserId);
  return users?.find((u) => u.id === userId) ?? null;
}

export function useDashboard() {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["dashboard", userId],
    queryFn: api.dashboard,
    enabled: !!userId,
  });
}

/* What a template mutation makes stale, in one place.
 *
 * Every one of these used to invalidate ["templates"], a key with no query behind it:
 * the list page it belonged to was deleted and the invalidations outlived it. Only
 * `useCloseTemplate` also invalidated ["dashboard"], so publishing a survey and going
 * home showed the old status, and deleting one left its row on the dashboard it had
 * just navigated to.
 *
 * The keys carry the acting user as their last element and are invalidated by prefix,
 * which matches every user's copy. That is intended: switching user in the dev picker
 * should not serve the previous author's dashboard. */
function invalidateTemplate(qc: ReturnType<typeof useQueryClient>, id?: string) {
  void qc.invalidateQueries({ queryKey: ["dashboard"] });
  if (id) void qc.invalidateQueries({ queryKey: ["template", id] });
}

/** Publishing and closing also change what a respondent can open. */
function invalidatePublished(qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: ["published-surveys"] });
}

export function useCloseTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.closeTemplate(id),
    onSuccess: (_data, id) => {
      invalidateTemplate(qc, id);
      invalidatePublished(qc);
    },
  });
}

export function useTemplate(id: string) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["template", id, userId],
    queryFn: () => api.getTemplate(id),
    enabled: !!userId,
  });
}

export function useReport(id: string) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["report", id, userId],
    queryFn: () => api.report(id),
    enabled: Boolean(userId),
  });
}

export function useCreateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TemplateWrite) => api.createTemplate(data),
    onSuccess: () => invalidateTemplate(qc),
  });
}

export function useUpdateTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TemplateWrite) => api.updateTemplate(id, data),
    onSuccess: () => invalidateTemplate(qc, id),
  });
}

export function useDeleteTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.deleteTemplate(id),
    // The builder navigates home on success, so a stale dashboard here means the
    // author lands on a list still showing the survey they just deleted.
    onSuccess: () => invalidateTemplate(qc),
  });
}

export function usePublishTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.publishTemplate(id),
    onSuccess: () => {
      invalidateTemplate(qc, id);
      invalidatePublished(qc);
    },
  });
}

export function useGenerateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    // An object rather than two positional arguments: the audience decides who may answer
    // the survey, and a bare second string is the kind of thing that gets passed in the
    // wrong order once and then silently aims a survey at the wrong people.
    mutationFn: ({
      prompt,
      audience,
      audienceUserId,
    }: {
      prompt: string;
      audience: SurveyAudience;
      audienceUserId?: string | null;
    }) => api.generateTemplate(prompt, audience, audienceUserId ?? null),
    onSuccess: () => invalidateTemplate(qc),
  });
}

export function useRefineTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (instruction: string) => api.refineTemplate(id, instruction),
    onSuccess: () => invalidateTemplate(qc, id),
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

export function useTemplateRuns(templateId: string) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["template-runs", templateId, userId],
    queryFn: () => api.listTemplateRuns(templateId),
    enabled: !!userId,
  });
}

export function useTemplateRun(templateId: string, runId: string | null) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["template-run", templateId, runId, userId],
    queryFn: () => api.getTemplateRun(templateId, runId as string),
    enabled: !!userId && !!runId,
  });
}

/** Every answer by respondent, unaggregated, so the page can slice and cross-tabulate
 *  without a request per response. */
export function useAnswersMatrix(templateId: string) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["answers", templateId, userId],
    queryFn: () => api.answersMatrix(templateId),
    enabled: !!userId,
  });
}

/** The recap already written, read back for free.
 *
 *  A query, unlike generating one, because reading costs no model call. Before this the
 *  page rendered the recap out of the mutation's own result, so leaving the tab and
 *  coming back lost it and the author paid again to read prose the column already had. */
export function useSurveyRecap(templateId: string) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["survey-recap", templateId, userId],
    queryFn: () => api.surveyRecap(templateId),
    enabled: !!userId,
  });
}

/** Writing a new recap. A mutation for the same reason the per-run one is: it costs
 *  model calls, so it happens when the author asks and never on render. */
export function useSummariseSurvey(templateId: string) {
  const qc = useQueryClient();
  const userId = useUserStore((s) => s.currentUserId);
  return useMutation({
    mutationFn: (refresh: boolean = false) => api.summariseSurvey(templateId, refresh),
    // Seeded into the key `useSurveyRecap` reads, in the envelope that hook returns.
    // It used to write a bare summary to this key and nothing read it at all, so the
    // write was dead and the recap lived only in mutation state.
    onSuccess: (summary) =>
      qc.setQueryData<SurveyRecapStatus>(["survey-recap", templateId, userId], {
        recap: summary,
        absence: null,
      }),
  });
}

/** Summarising is a model call the author asks for, so it is a mutation, not a query
 *  that fires on render. The result is written back into the cached run detail. */
export function useSummariseRun(templateId: string, runId: string | null) {
  const qc = useQueryClient();
  const userId = useUserStore((s) => s.currentUserId);
  return useMutation({
    mutationFn: (refresh: boolean = false) =>
      api.summariseRun(templateId, runId as string, refresh),
    onSuccess: (summary) =>
      qc.setQueryData(["template-run", templateId, runId, userId], (run: RunDetail | undefined) =>
        run ? { ...run, summary } : run,
      ),
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
