"use client";

import Link from "next/link";
import { useState } from "react";

import { LOCALES, isLocale, type Locale } from "@/lib/i18n";
import { useDocumentLanguage, useT } from "@/lib/i18n/useT";
import { useIdentify, useMe, useProviders, useUsers } from "@/lib/queries";
import { useLocaleStore, useUserStore } from "@/lib/store";

/**
 * The way into a browser that has never been here before.
 *
 * Deliberately an address rather than a list of who exists. The list is the thing that
 * needs a caller, and handing it out unauthenticated would mean handing out every id,
 * which under this shim is every credential.
 *
 * Scaffolding, and it should go when a real identity provider does. Nothing else on this
 * page will need changing when it does: only how the id is obtained changes.
 */
function SignIn() {
  const { topbar } = useT();
  const [email, setEmail] = useState("");
  const identify = useIdentify();
  const { data } = useProviders();
  const providers = data?.providers ?? [];
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  return (
    <>
      {/* Real sign-in, when the deployment has any. Plain links rather than fetches: the
          browser has to navigate to the provider, and an XHR cannot do that. Only
          configured providers appear, so no button here can fail for being unwired. */}
      {providers.length > 0 ? (
        <span className="topbar-signin">
          {providers.map((p) => (
            <a key={p} className="btn btn-primary" href={`${base}/api/v1/auth/${p}/login`}>
              {p === "microsoft" ? topbar.signInMicrosoft : topbar.signInGoogle}
            </a>
          ))}
        </span>
      ) : null}
      {/* The development shim, drawn only where the server mounts it. */}
      {data?.address_sign_in ? (
      <form
      className="topbar-signin"
      onSubmit={(e) => {
        e.preventDefault();
        if (email.trim()) identify.mutate(email.trim());
      }}
    >
      <label className="topbar-user-label" htmlFor="signin-email">
        {topbar.signInLabel}
      </label>
      <input
        id="signin-email"
        type="email"
        value={email}
        placeholder={topbar.signInPlaceholder}
        onChange={(e) => setEmail(e.target.value)}
        // The address is not a secret and the browser remembering it saves retyping it
        // on every fresh profile, which is the situation this whole control exists for.
        autoComplete="email"
      />
      <button type="submit" disabled={identify.isPending}>
        {identify.isPending ? topbar.signingIn : topbar.signIn}
      </button>
      {/* The server's own sentence, which for the case that matters names the address
          that was not found. */}
      {identify.error ? (
        <span className="topbar-signin-error">{identify.error.message}</span>
      ) : null}
      </form>
      ) : null}
    </>
  );
}

export function TopBar() {
  const { data: users } = useUsers();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const setCurrentUserId = useUserStore((s) => s.setCurrentUserId);
  const locale = useLocaleStore((s) => s.locale);
  const setLocale = useLocaleStore((s) => s.setLocale);
  const { topbar } = useT();
  const { data: me } = useMe();
  useDocumentLanguage();

  return (
    <header className="topbar">
      <div className="topbar-left">
        {/* One brand target for every role now that `/` explains the product rather than
            being the author's workspace. A respondent clicking it used to land on the
            dashboard's redirect; now it lands somewhere that reads as an answer to
            "what is this", which is what a first-time arrival is asking. */}
        <Link href="/" className="topbar-brand">
          {topbar.brandLead} <span>{topbar.brandTail}</span>
        </Link>
        <nav className="topbar-nav">
          <Link href="/">{topbar.home}</Link>
          <Link href="/respond">{topbar.respond}</Link>
          {/* Administrators only, and the server says who that is: the lens reads are
              refused to anyone else, so a link that led to a refusal would be a lie. */}
          {me?.is_admin ? <Link href="/lens">Lens</Link> : null}
        </nav>
      </div>
      <div className="topbar-user">
        {/* Nobody selected means the picker below is not merely empty, it is unfillable:
            listing users needs a caller, a caller is an id, and this dropdown was the
            only place to get one. So the first thing shown is a way in, not a dropdown
            with one disabled placeholder in it and every page telling you to use it. */}
        {currentUserId ? (
          <>
            <span className="topbar-user-label">{topbar.actingAs}</span>
            <select
              value={currentUserId}
              onChange={(e) => setCurrentUserId(e.target.value || null)}
            >
              <option value="">{topbar.selectUser}</option>
              {users?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.display_name} · {u.function ?? "-"}
                </option>
              ))}
            </select>
          </>
        ) : (
          <SignIn />
        )}
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
