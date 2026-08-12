"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AutoGrowTextarea } from "@/components/AutoGrowTextarea";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { groupForDashboard } from "@/lib/dashboardAttention";
import { useT } from "@/lib/i18n/useT";
import { useCurrentUser, useDashboard, useGenerateTemplate, useUsers } from "@/lib/queries";
import { useDraftNoteStore, useUserStore } from "@/lib/store";
import type { SurveyAudience } from "@/lib/types";

/**
 * The landing page, and the only page that renders for someone who has not picked a user.
 *
 * It used to be the dashboard, which meant the first thing a newcomer saw was either a
 * list of somebody else's surveys or a line telling them to pick a user, and nothing
 * anywhere said what the product was. The dashboard moved to `/dashboard`; what is here
 * is an explanation, with the compose bar on top of it for an author who is signed in.
 *
 * Nothing above the author panel is gated on a user, and `useDashboard` is already
 * `enabled: !!userId`, so a signed-out visit makes no authenticated request at all.
 */
export default function Home() {
  const { landing, home } = useT();
  // The store, not `useCurrentUser`, decides whether anyone is signed in. `useCurrentUser`
  // resolves the id against the user list, so it is null for the whole time that request
  // is in flight, and gating the hint on it would flash "pick a user" at an author who
  // already had.
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  // Already fetched for the top bar's user picker, so this is the same cached query
  // rather than a second request.
  const { data: users } = useUsers();
  const { data: rows } = useDashboard();
  const generate = useGenerateTemplate();
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [audience, setAudience] = useState<SurveyAudience>("everyone");
  const [audienceUserId, setAudienceUserId] = useState<string>("");
  const setPendingNote = useDraftNoteStore((s) => s.setPendingNote);

  const isAuthor = currentUser?.role === "author";
  const isRespondent = currentUser?.role === "respondent";
  const needsYou = rows ? groupForDashboard(rows).needsYou.length : 0;

  // A person must actually be chosen before the pair is valid. The server refuses
  // `person` with nobody named, so catching it here is the difference between a disabled
  // button and a 422 the author has to interpret.
  const needsPerson = audience === "person" && !audienceUserId;

  async function onGenerate() {
    if (!prompt.trim() || needsPerson) return;
    const { template, note } = await generate.mutateAsync({
      prompt: prompt.trim(),
      audience,
      // Only ever sent with `person`. Sending a stale id alongside a group audience is
      // the other half of the pairing the server rejects.
      audienceUserId: audience === "person" ? audienceUserId : null,
    });
    // Hand the note to the builder, then drop straight into it with the questions.
    if (note) setPendingNote(template.id, note);
    router.push(`/templates/${template.id}`);
  }

  // Named here rather than inline so the labels and the values cannot drift apart: the
  // union in lib/types.ts is what the API accepts, and a typo in one of these strings
  // would be a 422 the author reads as "generating is broken".
  const audiences: { value: SurveyAudience; label: string }[] = [
    { value: "everyone", label: landing.audienceEveryone },
    { value: "operatives", label: landing.audienceOperatives },
    { value: "line_leaders", label: landing.audienceLineLeaders },
    { value: "supervisors", label: landing.audienceSupervisors },
    { value: "managers", label: landing.audienceManagers },
    { value: "qa", label: landing.audienceQa },
    { value: "person", label: landing.audiencePerson },
  ];

  const steps = [
    { title: landing.step1Title, body: landing.step1Body },
    { title: landing.step2Title, body: landing.step2Body },
    { title: landing.step3Title, body: landing.step3Body },
  ];

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 p-4">
      <section className="flex flex-col gap-2">
        <h1 className="text-lg font-semibold text-ink">{landing.heroTitle}</h1>
        <p className="max-w-prose text-md text-muted">{landing.heroBody}</p>
      </section>

      {/* The compose bar, for an author only. Drafting needs an author identity on the
          backend, so showing the box to a visitor who has not picked a user would be an
          invitation to a 401. A respondent gets the way through to their own surveys
          instead, and a signed-out visitor gets the explanation and nothing to click. */}
      {isAuthor ? (
        <div className="flex flex-col gap-2 rounded-lg border border-ai-border bg-ai-fill p-3">
          <div>
            <h2 className="text-md font-semibold text-ink">{home.newSurvey}</h2>
            <p className="text-sm text-muted">{home.newSurveyHint}</p>
          </div>
          {/* No min-height utility: `.autogrow` in globals.css is unlayered and sets
              `min-height: 0`, and AutoGrowTextarea then writes `style.height` from
              scrollHeight, so an inline style has the last word anyway. The box starts at
              one line and grows as you type, which is what the component is for. */}
          <AutoGrowTextarea
            className="autogrow w-full rounded-md border border-line bg-raised px-2.5 py-2"
            placeholder={home.describePlaceholder}
            value={prompt}
            onChange={setPrompt}
          />
          {/* Who it is for, chosen with the description rather than after it. This is the
              only control anywhere in the app that sets `audience`: the builder carries
              the field on every save but has never rendered a way to change it. */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <label className="flex items-center gap-2 text-sm text-muted">
                {landing.audienceLabel}
                {/* No font-size or colour utility on the select: `input, textarea, select`
                    in globals.css is unlayered, so its `font-size: inherit` and `color`
                    beat any utility here. The size comes from the label's `text-sm`
                    through that inherit, which is the mechanism, not a coincidence to
                    rely on silently. */}
                <select
                  className="rounded-md border border-line bg-raised px-2 py-1"
                  value={audience}
                  onChange={(e) => setAudience(e.target.value as SurveyAudience)}
                >
                  {audiences.map((a) => (
                    <option key={a.value} value={a.value}>
                      {a.label}
                    </option>
                  ))}
                </select>
              </label>
              {/* Only when there is a person to choose. A permanently visible name picker
                  that does nothing for six of the seven audiences is a control that
                  teaches the reader to ignore it. */}
              {audience === "person" ? (
                <label className="flex items-center gap-2 text-sm text-muted">
                  {landing.personLabel}
                  <select
                    className="rounded-md border border-line bg-raised px-2 py-1"
                    value={audienceUserId}
                    onChange={(e) => setAudienceUserId(e.target.value)}
                  >
                    <option value="">{landing.personPlaceholder}</option>
                    {(users ?? []).map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.display_name}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
            </div>
            <Button
              variant="ai"
              onClick={onGenerate}
              disabled={generate.isPending || !prompt.trim() || needsPerson}
            >
              {generate.isPending ? home.drafting : home.generateDraft}
            </Button>
          </div>

          {/* Said out loud rather than left to be inferred. A survey with an audience of
              one is attributable however the results are labelled: the answers still
              carry a pseudonym, and with one person in the audience the pseudonym hides
              nothing. An author choosing this should know that before they send it. */}
          {audience === "person" ? (
            <p className="text-sm text-warn-text">{landing.attributable}</p>
          ) : null}
          {generate.error ? <ErrorBanner error={generate.error} /> : null}
        </div>
      ) : null}

      {/* One link back to the work, so an author who lands here on the way in is not
          stranded on a page that explains a product they already use. Only when there is
          something waiting: a standing "0 need you" is a nag with no action behind it. */}
      {isAuthor && needsYou > 0 ? (
        <Link href="/dashboard" className="text-sm text-warn-text">
          {landing.needsYou(needsYou)}
        </Link>
      ) : null}

      {isRespondent ? (
        <Card className="flex flex-wrap items-center justify-between gap-3 p-4">
          <p className="text-md text-ink">{landing.respondBody}</p>
          <Button variant="primary" asChild>
            <Link href="/respond">{landing.respondCta}</Link>
          </Button>
        </Card>
      ) : null}

      {!currentUserId ? <p className="text-sm text-muted">{landing.signedOutHint}</p> : null}

      {/* The video slot. Empty on purpose: there is no asset in the repo, and a committed
          mp4 is weight that never comes back out of git history. To fill it, replace the
          inner div with a <video> pointing at a file in `public/`, or with an iframe, and
          leave the aspect-ratio wrapper alone so the page does not reflow when it loads. */}
      <section className="flex flex-col gap-2">
        <h2 className="text-md font-semibold text-ink">{landing.videoTitle}</h2>
        {/* Capped rather than full width. At the page's max-w-5xl a 16:9 box is over 500px
            tall, which made an empty placeholder the largest thing on the page and pushed
            the three steps under the fold. A real video does not need to be wider than
            this either. */}
        <div
          className="flex aspect-video w-full max-w-2xl items-center justify-center rounded-lg border border-line bg-canvas"
          role="img"
          aria-label={landing.videoLabel}
        >
          <p className="text-sm text-muted">{landing.videoPlaceholder}</p>
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-md font-semibold text-ink">{landing.howTitle}</h2>
        {/* An ordered list, because the three are a sequence and not three features:
            a screen reader should get "1 of 3" without the number being drawn in. */}
        <ol className="grid gap-3 sm:grid-cols-3">
          {steps.map((step, i) => (
            <Card key={step.title} className="flex flex-col gap-1.5 p-4">
              <span className="text-xs font-semibold uppercase tracking-wide text-muted">
                {landing.stepNumber(i + 1)}
              </span>
              <h3 className="text-md font-semibold text-ink">{step.title}</h3>
              <p className="text-sm text-muted">{step.body}</p>
            </Card>
          ))}
        </ol>
      </section>
    </div>
  );
}
