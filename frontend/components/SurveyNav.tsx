"use client";

import Link from "next/link";

import { useT } from "@/lib/i18n/useT";

export type SurveyTab = "build" | "results";

/**
 * Where you are in a survey, and the other place you can be.
 *
 * Two tabs rather than three. Responses and Report were separate pages that answered
 * halves of one question: Report had the tallies with the respondent stripped out, and
 * Responses had the respondents with no way to see how one answer sat against the rest.
 * An author moving between them was doing the join by hand, and the tab strip made that
 * look like a choice rather than a gap.
 *
 * A `nav` with `aria-current` rather than buttons, because that is what this is: the
 * current page is marked for a screen reader the same way it is marked visually.
 *
 * Results is shown whatever the survey's state. A draft has none, and the page says so
 * plainly when opened; hiding the tab would make the strip change shape under an author
 * who published a moment ago, which is worse than a page that explains it is empty.
 */
export function SurveyNav({ templateId, current }: { templateId: string; current: SurveyTab }) {
  const { builder, common } = useT();
  const tabs: { key: SurveyTab; href: string; label: string }[] = [
    { key: "build", href: `/templates/${templateId}`, label: builder.tabBuild },
    { key: "results", href: `/templates/${templateId}/results`, label: builder.tabResults },
  ];

  return (
    <div className="survey-nav">
      <Link href="/dashboard" className="survey-back">
        {common.backToDashboard}
      </Link>
      <nav className="survey-tabs" aria-label={builder.tabsLabel}>
        {tabs.map((t) => (
          <Link
            key={t.key}
            href={t.href}
            className={t.key === current ? "survey-tab survey-tab-on" : "survey-tab"}
            aria-current={t.key === current ? "page" : undefined}
          >
            {t.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
