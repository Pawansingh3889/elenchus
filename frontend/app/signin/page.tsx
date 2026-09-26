"use client";

import { useEffect, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";

import { useT } from "@/lib/i18n/useT";
import { useProviders, useSession } from "@/lib/queries";

/**
 * The way in.
 *
 * Sign-in was a box in the top bar, which is the right size for a development shim and
 * the wrong size for the thing a person does first. This is a page: it says what the
 * service is called, offers the providers this deployment actually has, and says who to
 * ask when it will not let you in.
 *
 * **It cannot create an account, deliberately.** Every right in this system derives from
 * a job an administrator assigns, and an account created by a first sign-in holds no job:
 * it sits in no audience, can be surveyed by nobody, and quietly widens every
 * denominator until somebody notices. So an unknown address is refused with a sentence
 * naming the fix, rather than admitted into a half-state.
 *
 * It also cannot serve most of the plant yet, which is worth knowing rather than
 * discovering: the floor has no work email and no Microsoft account, and the way in for
 * them is a break-room kiosk with a works number and a PIN that does not exist.
 */
export default function SignIn() {
  const { signin, topbar } = useT();
  const router = useRouter();
  const { data } = useProviders();
  const { data: session } = useSession();
  const providers = data?.providers ?? [];
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  // Already signed in: this page has nothing to offer, and leaving it reachable would
  // let somebody sign in twice and wonder which one took.
  useEffect(() => {
    if (session) router.replace("/respond");
  }, [session, router]);

  // The refusal the callback redirects with. `useSyncExternalStore` rather than an
  // effect that sets state: the query string is browser-only, so this is the shape that
  // avoids both a hydration mismatch and a setState inside an effect.
  const search = useSyncExternalStore(
    () => () => {},
    () => window.location.search,
    () => "",
  );
  const reason = new URLSearchParams(search).get("sign_in_error");
  const said: Record<string, string> = {
    no_account: topbar.errNoAccount,
    state_mismatch: topbar.errRetry,
    expired: topbar.errRetry,
    no_code: topbar.errRetry,
    no_email: topbar.errNoEmail,
  };

  return (
    <div className="page narrow signin">
      <div>
        <h1>{signin.title}</h1>
        <p className="muted">{signin.subtitle}</p>
      </div>

      {/* Above the buttons, not below: somebody arriving here after a refusal needs the
          reason before they press the same button again. */}
      {reason ? (
        <p className="error-text" role="alert">
          {said[reason] ?? reason}
        </p>
      ) : null}

      <div className="card stack">
        {providers.length > 0 ? (
          // Plain links. The browser has to navigate to the provider, which an XHR
          // cannot do, and only configured providers appear, so no button here can fail
          // for being unwired.
          providers.map((p) => (
            <a
              key={p}
              className="btn btn-primary"
              href={`${base}/api/v1/auth/${p}/login`}
            >
              {p === "microsoft" ? topbar.signInMicrosoft : topbar.signInGoogle}
            </a>
          ))
        ) : (
          // A deployment with no provider configured has no way in at all, which is the
          // correct failure and a confusing one to meet without an explanation.
          <p className="muted">{signin.noProviders}</p>
        )}
      </div>

      {/* On an open deployment the first sign-in is the sign-up, so the page says that and
          says what is kept, instead of sending a stranger to an administrator. */}
      <div>
        <h2>{data?.open_sign_up ? signin.openTitle : signin.noAccountTitle}</h2>
        <p className="muted">{data?.open_sign_up ? signin.openBody : signin.noAccountBody}</p>
      </div>
    </div>
  );
}
