"use client";

import Link from "next/link";

import { useUsers } from "@/lib/queries";
import { useUserStore } from "@/lib/store";

export function TopBar() {
  const { data: users } = useUsers();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const setCurrentUserId = useUserStore((s) => s.setCurrentUserId);

  return (
    <header className="topbar">
      <Link href="/" className="topbar-brand">
        ViewOps <span>Surveys</span>
      </Link>
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
