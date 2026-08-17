"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n/useT";

/**
 * What a signed-out visitor sees on a page that needs them.
 *
 * Every such page used to render a sentence telling the reader to pick a user in a
 * control they may not have noticed, which was fair enough while the only way in was a
 * dropdown in the top bar. There is a sign-in page now, so these pages point at it.
 *
 * A component rather than a redirect: a page that bounces you elsewhere loses where you
 * were trying to go, and this keeps the address you asked for so a browser back button
 * still means something.
 */
export function SignInPrompt() {
  const { signin } = useT();
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-3 p-6 pt-16 text-center">
      <h1 className="text-lg font-semibold text-ink">{signin.title}</h1>
      <p className="text-sm text-muted">{signin.needsSignIn}</p>
      <Button variant="primary" asChild>
        <Link href="/signin">{signin.goToSignIn}</Link>
      </Button>
    </div>
  );
}
