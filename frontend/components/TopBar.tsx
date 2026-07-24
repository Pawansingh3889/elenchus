"use client";

import Link from "next/link";

import { useUsers } from "@/lib/queries";
import { useUserStore } from "@/lib/store";

export function TopBar() {
  const { data: users } = useUsers();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const setCurrentUserId = useUserStore((s) => s.setCurrentUserId);
  // The nav must follow the acting user's role: Build pages are author-only on the
  // backend, so showing the link to a respondent just leads to a 403.
  const currentUser = users?.find((u) => u.id === currentUserId);
  const isAuthor = currentUser?.role === "author";

  return (
    <header className="topbar">
      <div className="topbar-left">
        <Link href={isAuthor ? "/" : "/respond"} className="topbar-brand">
          ViewOps <span>Surveys</span>
        </Link>
        <nav className="topbar-nav">
          {isAuthor && <Link href="/">Build</Link>}
          <Link href="/respond">Respond</Link>
        </nav>
      </div>
      <div className="topbar-user">
        <span className="topbar-user-label">Acting as</span>
        <select
          value={currentUserId ?? ""}
          onChange={(e) => setCurrentUserId(e.target.value || null)}
        >
          <option value="">Select a user…</option>
          {users?.map((u) => (
            <option key={u.id} value={u.id}>
              {u.display_name} · {u.role}
            </option>
          ))}
        </select>
      </div>
    </header>
  );
}
