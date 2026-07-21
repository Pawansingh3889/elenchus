"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./api";
import { useUserStore } from "./store";
import type { TemplateWrite } from "./types";

export function useUsers() {
  return useQuery({ queryKey: ["users"], queryFn: api.listUsers });
}

export function useTemplates() {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["templates", userId],
    queryFn: api.listTemplates,
    enabled: !!userId,
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

export function useSendRunMessage(id: string) {
  const qc = useQueryClient();
  const userId = useUserStore((s) => s.currentUserId);
  return useMutation({
    mutationFn: (content: string) => api.sendRunMessage(id, content),
    // The turn returns the whole updated run, so seed the cache rather than refetch it.
    onSuccess: (run) => qc.setQueryData(["run", id, userId], run),
  });
}
