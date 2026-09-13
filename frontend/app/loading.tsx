/** Shown while a route segment loads. Plain on purpose: the pages it stands in for are
 *  short, and a skeleton shaped like a dashboard outlived the dashboard. */
export default function Loading() {
  return <p className="empty" aria-busy="true">Loading…</p>;
}
