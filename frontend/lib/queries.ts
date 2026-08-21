"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { api } from "./api";
import { useUserStore } from "./store";
import type {
  AccountCreate,
  AccountWrite,
  RunDetail,
  SurveyAudience,
  SurveyRecapStatus,
  TemplateWrite,
} from "./types";

export function useUsers() {
  const userId = useUserStore((s) => s.currentUserId);
  // Not fetched until somebody is acting, because without an id this request cannot
  // succeed: the endpoint requires a caller and the browser has none to send. Firing it
  // anyway meant every cold load spent a request to be told 401 and logged a console
  // error for it, which is a real failure sitting in the overlay on a page that is
  // working exactly as intended.
  return useQuery({ queryKey: ["users"], queryFn: api.listUsers, enabled: !!userId });
}

/** The acting user's record (id + role), for role-gating nav and pages. */
/** Everyone, with where they sit. Author-only on the server; the page is gated too
 *  so a respondent gets a line rather than a 403 banner. */
export function usePeople() {
  return useQuery({ queryKey: ["people"], queryFn: api.listPeople });
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
    if (query.data) setCurrentUserId(query.data.id);
  }, [query.data, setCurrentUserId]);
  return query;
}

export function useCurrentUser() {
  const { data: users } = useUsers();
  const { data: session } = useSession();
  const userId = useUserStore((s) => s.currentUserId);
  // The session first, because it is the one the server will actually act on. The
  // picker scan is the development path, and it is a scan rather than a fetch because
  // the same list draws the picker itself.
  return session ?? users?.find((u) => u.id === userId) ?? null;
}

/** The caller as the server sees them, chiefly whether they administer anything.
 *
 * Beside `useCurrentUser` rather than replacing it. That one scans the dev-auth picker,
 * which is also what populates the picker itself, so it has a second job here. This one
 * asks the server a question the browser cannot answer: half of `is_admin` is an email
 * allowlist in server settings, so a client deciding it locally would decide it wrongly
 * for every administrator who is not in the IT department.
 */
export function useMe() {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({ queryKey: ["me", userId], queryFn: api.me, enabled: !!userId });
}

/* What an account mutation makes stale.
 *
 * `["users"]` is the one that is easy to forget and the most visible when it is missing.
 * It backs the acting-as picker in the top bar, and the top bar decides from it whether
 * to show the author nav at all. Without this line a person you just created does not
 * appear in the picker until a hard reload, so the account exists and there is no way to
 * become it: the screen looks broken rather than slow. Found by using the screen.
 *
 * `["people"]` is the directory the row itself came from, and `["dashboard"]` because
 * every reach number is computed over the people who exist.
 */
function invalidateAccounts(qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: ["users"] });
  void qc.invalidateQueries({ queryKey: ["people"] });
  void qc.invalidateQueries({ queryKey: ["dashboard"] });
  // Reach is live, so an account change moves it; and the edit that just landed is the
  // newest row of its own history. Prefix keys, so every user's copies go together.
  void qc.invalidateQueries({ queryKey: ["audience-reach"] });
  void qc.invalidateQueries({ queryKey: ["account-history"] });
}

/** Live headcount per audience. `enabled` keeps it off the wire until a screen actually
 *  shows the number, which for the publish dialog is the moment it opens. */
export function useAudienceReach(enabled: boolean) {
  return useQuery({
    queryKey: ["audience-reach"],
    queryFn: api.audienceReach,
    enabled,
  });
}

export function useAccountHistory(userId: string | null) {
  return useQuery({
    queryKey: ["account-history", userId],
    queryFn: () => api.accountHistory(userId as string),
    enabled: !!userId,
  });
}

/** The what-if, as a mutation because it carries a body, although it writes nothing. */
export function usePreviewAccount() {
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AccountWrite }) =>
      api.previewAccount(id, data),
  });
}

export function useCreateAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AccountCreate) => api.createAccount(data),
    onSuccess: () => invalidateAccounts(qc),
  });
}

export function useReplaceAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AccountWrite }) =>
      api.replaceAccount(id, data),
    onSuccess: () => {
      invalidateAccounts(qc);
      // Editing your own account changes what the nav and this page may show you.
      void qc.invalidateQueries({ queryKey: ["me"] });
    },
  });
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

export function useLlmReport() {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["llm-report", userId],
    queryFn: api.llmReport,
    enabled: !!userId,
  });
}

export function useLlmRunEntries(runId: string | null) {
  const userId = useUserStore((s) => s.currentUserId);
  return useQuery({
    queryKey: ["llm-run-entries", runId, userId],
    queryFn: () => api.llmRunEntries(runId!),
    enabled: !!userId && !!runId,
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
