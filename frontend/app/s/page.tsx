"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { demo, useLinkToken } from "@/lib/demo";
import { useUserStore } from "@/lib/store";

export default function SurveyInvitation() {
  const token = useLinkToken();
  const router = useRouter();
  const qc = useQueryClient();
  const preview = useQuery({ queryKey: ["invitation", token], queryFn: () => demo.preview(token), enabled: !!token, retry: false });
  const enter = useMutation({ mutationFn: () => demo.participate(token), onSuccess: ({ user, run_id }) => {
    qc.clear();
    useUserStore.getState().setCurrentUserId(user.id);
    qc.setQueryData(["session"], user);
    window.history.replaceState(null, "", "/s");
    router.push(run_id ? `/runs/${run_id}` : "/respond");
  } });
  return <div className="product-page narrow-page"><section className="product-card">
    <p className="eyebrow">A MOMENT TO BE HEARD</p>
    <h1>{preview.data?.title ?? "Your survey invitation"}</h1>
    {!token && <p>Open the complete invitation link your survey organiser sent you.</p>}
    {preview.isFetching && <p role="status">Opening your invitation…</p>}
    {preview.error && <p role="alert">{preview.error.message}</p>}
    {preview.data && <>
      <p>{preview.data.description}</p><p>{preview.data.questions} questions, at your own pace. You can pause and return in this browser.</p>
      <div className="notice"><h2>Before you begin</h2><p>{preview.data.disclosure}</p><p>Your responses are processed by an AI interviewer. The organiser can read the conversation. You can withdraw your response from the chat.</p></div>
      <form onSubmit={event => { event.preventDefault(); enter.mutate(); }}>
        <label className="check-label"><input type="checkbox" required /> I understand how my response will be used and want to take part.</label>
        <button className="btn btn-primary" disabled={enter.isPending}>{enter.isPending ? "Starting…" : "Start or resume survey"}</button>
      </form>
      <p className="muted">This opens a participant session in this browser. If you also create surveys, use a separate browser profile to keep your author session open.</p>
    </>}
    {enter.error && <p role="alert" className="error-text">{enter.error.message}</p>}
    <Link href="/">About Elenchus</Link>
  </section></div>;
}
