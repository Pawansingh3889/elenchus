/**
 * Who a survey can be aimed at, in the order the builder offers them.
 *
 * `respondents` is the whole respondent pool, which is what every survey was before
 * audiences existed and so is what an unaimed draft means. The rest name a creator
 * department, and a survey aimed at one is answered by the creators in it.
 *
 * Frozen once published, because the audience is part of what was published: a survey
 * that collects Finance answers and is then pointed at HR ends up with one set of
 * results drawn from two populations, with nothing in the data recording that it moved.
 */
import type { SurveyAudience } from "@/lib/types";

export const AUDIENCES: { value: SurveyAudience; label: string }[] = [
  { value: "respondents", label: "Everyone (respondent pool)" },
  { value: "hr", label: "HR" },
  { value: "operations", label: "Operations" },
  { value: "finance", label: "Finance" },
  { value: "technical", label: "Technical" },
];
