"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AutoGrowTextarea } from "@/components/AutoGrowTextarea";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { audienceLabel } from "@/lib/audience";
import { groupForDashboard, landingFor, type Attention } from "@/lib/dashboardAttention";
import { useT } from "@/lib/i18n/useT";
import { useCurrentUser, useDashboard, useGenerateTemplate, useUsers } from "@/lib/queries";
import { useDraftNoteStore, useUserStore } from "@/lib/store";
import type { DashboardRow, SurveyAudience } from "@/lib/types";

/**
 * The landing page, and the only page that renders for someone who has not signed in.
 *
 * It serves two people who want opposite things, and it used to serve only the second.
 * An author signing in got a hero explaining a product they use every day, with the box
 * they came to type in below it and their outstanding work a text link further down
 * still. Nielsen Norman's finding on personalisation is that personalised content placed
 * under generic content is measurably less discoverable, and the guidance for internal
 * tools is that a product home is a contextual index: what is here, and where next. So
 * the page now branches on who is reading it.
 *
 * **An author sees their work.** The compose box is the hero rather than something below
 * it, because starting a survey is the one thing this page exists to let them do.
 * Underneath is what needs them and what they have running, which is the dashboard's
 * headline rather than its whole table: enough to decide whether to go there.
 *
 * **Everyone else sees the explanation**, which is the page this used to be for
 * everybody: what the service is, a video of it working, and the three steps.
 *
 * **An author with no surveys yet counts as everyone else**, and gets both. Their
 * account says author and their screen would otherwise say nothing at all, which is the
 * emptiest possible first impression of a product whose whole pitch is that it drafts
 * the thing for you.
 *
 * Nothing above the author panel is gated on a user, and `useDashboard` is already
 * `enabled: !!userId`, so a signed-out visit still makes no authenticated request.
 */
export default function Home() {
  const { landing, audience: aud, home } = useT();
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

  const isAuthor = currentUser?.may_author === true;
  const isRespondent = currentUser ? !currentUser.may_author : false;

  const grouped = rows ? groupForDashboard(rows) : null;
  const needsYou = grouped?.needsYou ?? [];
  // The API sends the author's own recency, which is the order the dashboard trusts for
  // its running group, so "recent" is the front of the list rather than a second sort.
  // Minus whatever is already above it: the first build showed the same survey twice,
  // once because it needed the author and again because it was recent, which spends two
  // tiles saying one thing and makes the second group look like a duplicate of the
  // first rather than the rest of the work.
  const needsIds = new Set(needsYou.map((n) => n.row.id));
  const recent = (rows ?? []).filter((r) => !needsIds.has(r.id)).slice(0, 4);
  // `rows` is undefined while the request is in flight and `[]` only once it has come
  // back empty. Reading the first as the second would flash the newcomer's explainer at
  // an author with thirty surveys on every reload.
  const authorHasNothing = isAuthor && rows !== undefined && rows.length === 0;
  // Who the explanation is for: anyone who is not a working author. A respondent gets it
  // too, because "what is this thing asking me questions" is a fair question from them.
  const showExplainer = !isAuthor || authorHasNothing;

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

  // The order the picker offers, with the labels coming from `audienceLabel` so this list
  // and the publish confirmation cannot disagree about what a group is called.
  const audiences: SurveyAudience[] = [
    "everyone",
    "operatives",
    "line_leaders",
    "supervisors",
    "shift_managers",
    "managers",
    "qa",
    "person",
  ];

  const steps = [
    { title: landing.step1Title, body: landing.step1Body },
    { title: landing.step2Title, body: landing.step2Body },
    { title: landing.step3Title, body: landing.step3Body },
  ];

  // The same two lines the dashboard puts under a row, read from the same helpers, so a
  // survey cannot describe itself one way here and another way one click later.
  const reachLine = (r: DashboardRow) =>
    r.reach > 0 ? home.ofPeople(r.people_completed, r.reach) : home.noResponses;

  const why = (row: DashboardRow, attention: Attention) => {
    if (attention === "resultsReady") return home.whyResultsReady;
    if (attention === "nobodyYet") return home.whyNobodyYet;
    if (attention === "stalled") return home.whyStalled(row.in_progress);
    return home.whyNotPublished;
  };

  const tile = (row: DashboardRow, line: string, flagged = false) => (
    <Card key={row.id} className="home-tile p-0">
      <Link
        href={landingFor(row)}
        className="flex h-full flex-col gap-1 p-4 no-underline"
        // The whole tile is the target, not the title inside it. A card-shaped thing
        // with a small link in it is a card that fails to be clicked.
      >
        <span className="line-clamp-2 text-md font-semibold text-ink">{row.title}</span>
        <span className={flagged ? "text-sm text-warn-text" : "text-sm text-muted"}>{line}</span>
      </Link>
    </Card>
  );

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 p-4">
      {/* The hero, which is whatever the reader came for. One surface, three contents:
          the compose box for an author, the pitch for a visitor, the way through for a
          respondent. Making it one element rather than three sections keeps the page
          from having a different shape for every kind of reader, which is what made the
          old one feel like two pages stapled together. */}
      <section className="home-hero flex flex-col gap-3">
        {isAuthor ? (
          <>
            <div className="flex flex-col gap-1">
              <h1 className="home-display">{landing.composeTitle}</h1>
              <p className="home-hero-sub max-w-prose text-md">{home.newSurveyHint}</p>
            </div>

            {/* No min-height utility: `.autogrow` in globals.css is unlayered and sets
                `min-height: 0`, and AutoGrowTextarea then writes `style.height` from
                scrollHeight, so an inline style has the last word anyway. The box starts
                at one line and grows as you type, which is what the component is for. */}
            <AutoGrowTextarea
              className="autogrow w-full rounded-lg border border-line bg-raised px-3 py-2.5 text-ink"
              placeholder={home.describePlaceholder}
              value={prompt}
              onChange={setPrompt}
            />

            {/* Who it is for, chosen with the description rather than after it. This is
                the only control anywhere in the app that sets `audience`: the builder
                carries the field on every save but has never rendered a way to change
                it. */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <label className="home-hero-sub flex items-center gap-2 text-sm">
                  {aud.label}
                  {/* No font-size or colour utility on the select: `input, textarea,
                      select` in globals.css is unlayered, so its `font-size: inherit`
                      and `color` beat any utility here. The size comes from the label's
                      `text-sm` through that inherit, which is the mechanism, not a
                      coincidence to rely on silently. */}
                  <select
                    className="rounded-md border border-line bg-raised px-2 py-1"
                    value={audience}
                    onChange={(e) => setAudience(e.target.value as SurveyAudience)}
                  >
                    {audiences.map((a) => (
                      <option key={a} value={a}>
                        {audienceLabel(aud, a)}
                      </option>
                    ))}
                  </select>
                </label>
                {/* Only when there is a person to choose. A permanently visible name
                    picker that does nothing for six of the seven audiences is a control
                    that teaches the reader to ignore it. */}
                {audience === "person" ? (
                  <label className="home-hero-sub flex items-center gap-2 text-sm">
                    {aud.personLabel}
                    <select
                      className="rounded-md border border-line bg-raised px-2 py-1"
                      value={audienceUserId}
                      onChange={(e) => setAudienceUserId(e.target.value)}
                    >
                      <option value="">{aud.personPlaceholder}</option>
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
                variant="primary"
                className="home-cta"
                onClick={onGenerate}
                disabled={generate.isPending || !prompt.trim() || needsPerson}
              >
                {generate.isPending ? home.drafting : home.generateDraft}
              </Button>
            </div>

            {/* Said out loud rather than left to be inferred. A survey with an audience
                of one is attributable however the results are labelled: the answers still
                carry a pseudonym, and with one person in the audience the pseudonym hides
                nothing. An author choosing this should know that before they send it. */}
            {audience === "person" ? (
              <p className="rounded-md bg-warn-fill px-2 py-1 text-sm text-warn-text">
                {aud.attributable}
              </p>
            ) : null}
            {generate.error ? <ErrorBanner error={generate.error} /> : null}
          </>
        ) : isRespondent ? (
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h1 className="home-display max-w-prose">{landing.respondBody}</h1>
            <Button variant="primary" className="home-cta" asChild>
              <Link href="/respond">{landing.respondCta}</Link>
            </Button>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <h1 className="home-display max-w-[18ch]">{landing.heroTitle}</h1>
            <p className="home-hero-sub max-w-prose text-md">{landing.heroBody}</p>
            {/* A signed-out visitor gets somewhere to go rather than a sentence telling
                them a control exists. The sign-in page has been the way in since it
                replaced the box in the top bar. */}
            {!currentUserId ? (
              <div>
                <Button variant="primary" className="home-cta" asChild>
                  <Link href="/signin">{landing.signInCta}</Link>
                </Button>
              </div>
            ) : null}
          </div>
        )}
      </section>

      {/* An author's own work, and only an author's. Two groups at most, four tiles at
          most: this is the headline of the dashboard, not a copy of it, and a home page
          that lists thirty surveys is the dashboard with a compose box on top. */}
      {isAuthor && needsYou.length > 0 ? (
        <section className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <h2 className="text-md font-semibold text-ink">{home.groupNeedsYou}</h2>
            <Badge variant="warn">{needsYou.length}</Badge>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {needsYou.slice(0, 3).map(({ row, why: attention }) =>
              tile(row, why(row, attention), true),
            )}
          </div>
        </section>
      ) : null}

      {isAuthor && recent.length > 0 ? (
        <section className="flex flex-col gap-3">
          <h2 className="text-md font-semibold text-ink">{landing.recentTitle}</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {recent.map((row) => tile(row, reachLine(row)))}
          </div>
        </section>
      ) : null}

      {/* The way through to the whole list, and its own row rather than a link in the
          "Your surveys" header. It sat there in the first build and vanished with that
          section, which happens whenever every survey an author has needs them: the two
          groups above were full and the only route onward had gone. */}
      {isAuthor && rows !== undefined && rows.length > 0 ? (
        <div>
          <Link href="/dashboard" className="text-sm text-accent-strong">
            {landing.allSurveys}
          </Link>
        </div>
      ) : null}

      {/* An author whose account works but whose dashboard is empty. Said plainly, above
          the explainer they are about to be shown, so the explainer reads as an answer
          to their situation rather than as marketing copy on their own home page. */}
      {authorHasNothing ? (
        <p className="text-md text-muted">{landing.newAuthorLead}</p>
      ) : null}

      {showExplainer ? (
        <>
          {/* The video slot, filled. `public/walkthrough.mp4` is a screencast of this app
              being used for real: the dashboard, a survey's results and recap, then a
              respondent answering in the chat while the engine and the model take their
              own time. Nothing in it is staged, which is the only reason it is worth
              1.7MB of repo weight, the cost this slot sat empty to avoid. Re-record it
              rather than editing around it. */}
          <section className="flex flex-col gap-2">
            <h2 className="text-md font-semibold text-ink">{landing.videoTitle}</h2>
            {/* Capped rather than full width. At the page's max-w-5xl a 16:9 box is over
                500px tall, which made an empty placeholder the largest thing on the page
                and pushed the three steps under the fold. A real video does not need to
                be wider than this either. */}
            <video
              className="aspect-video w-full max-w-2xl rounded-lg border border-line bg-canvas"
              controls
              // Nothing is fetched until it is asked for: the file is the heaviest thing
              // on a page whose whole job is to load fast for someone who has never been
              // here.
              preload="none"
              poster="/walkthrough-poster.jpg"
              playsInline
              aria-label={landing.videoLabel}
            >
              <source src="/walkthrough.mp4" type="video/mp4" />
              {landing.videoUnsupported}
            </video>
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
        </>
      ) : null}
    </div>
  );
}
