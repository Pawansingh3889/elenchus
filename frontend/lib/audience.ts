import type { Messages } from "./i18n/en";
import type { SurveyAudience } from "./types";

/**
 * What to call an audience, in one place.
 *
 * The picker on the landing page and the publish confirmation both have to name who a
 * survey is for, and two copies of the mapping is two places for a new group to be
 * half-added. An exhaustive `switch` over the union is what makes that a compile error
 * rather than a silent gap: add a value to `SurveyAudience` and this stops type-checking,
 * which is the frontend's version of the backend's `_AUDIENCE_GROUP` completeness test.
 *
 * `personName` is the display name when the survey names somebody. It falls back to the
 * generic "one person" rather than rendering an id or an empty string, because the user
 * list may not have arrived yet and a blank is worse than a vaguer truth.
 */
export function audienceLabel(
  aud: Messages["audience"],
  audience: SurveyAudience,
  personName?: string | null,
): string {
  switch (audience) {
    case "everyone":
      return aud.everyone;
    case "operatives":
      return aud.operatives;
    case "line_leaders":
      return aud.lineLeaders;
    case "supervisors":
      return aud.supervisors;
    case "managers":
      return aud.managers;
    case "qa":
      return aud.qa;
    case "person":
      return personName || aud.person;
  }
}
