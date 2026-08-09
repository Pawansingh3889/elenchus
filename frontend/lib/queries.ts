"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./api";
import { useUserStore } from "./store";
import type { RunDetail, TemplateWrite } from "./types";

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

export function useCloseTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.closeTemplate(id),
    onSuccess: (_data, id) => {
      // The dashboard shows the status, the template page shows it too, and the
      // template list is what Build renders. All three are stale the moment this lands.
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["template", id] });
      qc.invalidateQueries({ queryKey: ["templates"] });
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
  });
}

export function useUpdateTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TemplateWrite) => api.updateTemplate(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["template", id] });
      qc.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

export function useDeleteTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.deleteTemplate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
  });
}

export function usePublishTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.publishTemplate(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["template", id] });
      qc.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

export function useGenerateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (prompt: string) => api.generateTemplate(prompt),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
  });
}

export function useRefineTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (instruction: string) => api.refineTemplate(id, instruction),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["template", id] });
      qc.invalidateQueries({ queryKey: ["templates"] });
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
  return useMutation({ mutationFn: (templateId: string) => api.startRun(templateId) });
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
