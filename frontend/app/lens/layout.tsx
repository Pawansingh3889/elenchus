import { Suspense, type ReactNode } from "react";

import { LensNav } from "@/components/lens/LensNav";

/** One frame for every lens page: the tabs, then the filter row, then the page. The
 *  Suspense boundary is required because the filter reads the URL's search params. */
export default function LensLayout({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<p className="empty">Loading…</p>}>
      <LensNav />
      {children}
    </Suspense>
  );
}
