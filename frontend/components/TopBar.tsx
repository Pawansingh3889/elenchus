"use client";

import Link from "next/link";

import { LOCALES, isLocale, type Locale } from "@/lib/i18n";
import { useDocumentLanguage, useT } from "@/lib/i18n/useT";
import { useUsers } from "@/lib/queries";
import { useLocaleStore, useUserStore } from "@/lib/store";

export function TopBar() {
  const { data: users } = useUsers();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const setCurrentUserId = useUserStore((s) => s.setCurrentUserId);
  const locale = useLocaleStore((s) => s.locale);
  const setLocale = useLocaleStore((s) => s.setLocale);
  const { topbar } = useT();
  // The top bar is on every page, so it is the one place that can own the document's
  // language and direction without a provider wrapping the tree twice.
  useDocumentLanguage();

  // The nav must follow the acting user's role: Build pages are author-only on the
  // backend, so showing the link to a respondent just leads to a 403.
  const currentUser = users?.find((u) => u.id === currentUserId);
  const isAuthor = currentUser?.role === "author";

  return (
    <header className="topbar">
      <div className="topbar-left">
        <Link href={isAuthor ? "/" : "/respond"} className="topbar-brand">
          {topbar.brandLead} <span>{topbar.brandTail}</span>
        </Link>
        <nav className="topbar-nav">
          {/* Roles don't cross: authors build, respondents answer. */}
          {isAuthor ? (
            <Link href="/">{topbar.build}</Link>
          ) : (
            <Link href="/respond">{topbar.respond}</Link>
          )}
        </nav>
      </div>
      <div className="topbar-user">
        <span className="topbar-user-label">{topbar.actingAs}</span>
        <select
          value={currentUserId ?? ""}
          onChange={(e) => setCurrentUserId(e.target.value || null)}
        >
          <option value="">{topbar.selectUser}</option>
          {users?.map((u) => (
            <option key={u.id} value={u.id}>
              {u.display_name} · {u.role}
            </option>
          ))}
        </select>
        <select
          aria-label={topbar.language}
          value={locale}
          onChange={(e) => {
            const next = e.target.value;
            if (isLocale(next)) setLocale(next as Locale);
          }}
        >
          {Object.entries(LOCALES).map(([code, { label }]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </select>
      </div>
    </header>
  );
}
