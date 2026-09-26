"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { demo, useLinkToken } from "@/lib/demo";
import { useUserStore } from "@/lib/store";

export default function DemoEntry() {
  const token = useLinkToken();
  const router = useRouter();
  const qc = useQueryClient();
  const options = useQuery({ queryKey: ["demo-options"], queryFn: demo.options });
  const enter = useMutation({
    mutationFn: demo.enter,
    onSuccess: ({ user }) => {
      qc.clear();
      useUserStore.getState().setCurrentUserId(user.id);
      qc.setQueryData(["session"], user);
      window.history.replaceState(null, "", "/demo");
      router.push("/workspace");
    },
  });
  return <div className="product-page entry-page">
    <section className="product-intro"><p className="eyebrow">YOUR PRIVATE TRIAL</p><h1>From a question<br />to a clearer next step.</h1><p>Use your personal demo pass to create surveys, collect real responses, and explore the findings.</p>
      <ol className="entry-steps"><li><strong>Three surveys.</strong> Edit freely before publishing.</li><li><strong>Twenty respondent sessions each.</strong> Share a link without a sign-in step.</li><li><strong>Fourteen days.</strong> Read results and download them after the trial ends.</li></ol>
      <p>No payment details. Full access is included with a qualifying KapkotiSolution product, with an agreed monthly response-session allowance.</p>
      <Link href="/#walkthrough">Explore the sample without a pass →</Link>
    </section>
    <section className="product-card"><h2>Enter your workspace</h2><p>A pass grants access to your company workspace. Keep it private.</p>
      <form onSubmit={event => { event.preventDefault(); const value = new FormData(event.currentTarget).get("token"); if (typeof value === "string") enter.mutate(value.trim()); }}>
        <label htmlFor="demo-pass">Demo or customer pass</label><textarea key={token} defaultValue={token} id="demo-pass" name="token" required rows={3} autoComplete="off" spellCheck={false} />
        <button className="btn btn-primary" disabled={enter.isPending || !options.data?.enabled}>{enter.isPending ? "Opening workspace…" : "Enter workspace"}</button>
      </form>
      {enter.error && <p role="alert" className="error-text">{enter.error.message}</p>}
      {options.error && <p role="alert">{options.error.message}</p>}
      {options.data?.enabled === false && <p role="status">Private trials are not open on this deployment yet. You can still explore the interactive sample.</p>}
      <hr /><h3>Need a pass?</h3><p>Email your name, company, and what you want to learn. A person will arrange your trial.</p>
      <a className="btn" href="mailto:pawankapkoti3889@gmail.com?subject=Elenchus%20demo%20pass">Request a demo pass</a>
      <p className="muted">Later: an assistant will collect these details and arrange access after email verification.</p>
      <Link href="/signin">Already have a company sign-in?</Link>
    </section>
  </div>;
}
