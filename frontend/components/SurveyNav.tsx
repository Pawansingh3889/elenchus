"use client";

import Link from "next/link";

import { useT } from "@/lib/i18n/useT";

export type SurveyTab = "build" | "responses" | "report";

/**
 * Where you are in a survey, and the two other places you can be.
 *
 * The three pages used to reach each other through whatever buttons each had happened to
 * grow. Results could get to the builder and not to the report; the report could reach
 * both; every "back" went to the builder, including from a survey with eight responses;
 * and no page linked to the dashboard at all, so the only way out was the top bar. Three
 * pages about one survey with three different ideas of what the others were.
 *
 * A `nav` with `aria-current` rather than three buttons, because that is what this is:
 * the current page is marked for a screen reader the same way it is marked visually.
 *
 * Responses and Report are shown whatever the survey's state. A draft has neither, and
 * both pages say so plainly when opened; hiding them would make the tab strip change
 * shape under an author who published a moment ago, which is worse than a page that
 * explains it is empty.
 */
export function SurveyNav({ templateId, current }: { templateId: string; current: SurveyTab }) {
  const { builder, common } = useT();
  const tabs: { key: SurveyTab; href: string; label: string }[] = [
    { key: "build", href: `/templates/${templateId}`, label: builder.tabBuild },
    { key: "responses", href: `/templates/${templateId}/results`, label: builder.responses },
    { key: "report", href: `/templates/${templateId}/report`, label: builder.report },
  ];

  return (
    <div className="survey-nav">
      <Link href="/" className="survey-back">
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
