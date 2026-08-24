import type { DashboardRow } from "./types";

export interface SurveyAlert {
  surveyId: string;
  surveyTitle: string;
  severity: "critical" | "warning" | "info" | "success";
  type: string;
  message: string;
  value?: number;
  threshold?: number;
}

/**
 * Detect issues with surveys based on performance metrics
 */
export function detectSurveyAlerts(rows: DashboardRow[]): SurveyAlert[] {
  const alerts: SurveyAlert[] = [];
  const now = new Date();

  for (const row of rows) {
    // Skip draft surveys - they don't have response data yet
    if (row.status === "draft") continue;

    // Critical: Very low response rate (< 20%) for published surveys
    if (row.status === "published" && row.response_rate !== null && row.response_rate < 0.2) {
      alerts.push({
        surveyId: row.id,
        surveyTitle: row.title,
        severity: "critical",
        type: "low_response_rate",
        message: "Very low response rate",
        value: Math.round(row.response_rate * 100),
        threshold: 20
      });
    }

    // Critical: High abandonment rate (> 50% of started surveys not completed)
    if (row.started > 0 && row.abandoned / row.started > 0.5) {
      alerts.push({
        surveyId: row.id,
        surveyTitle: row.title,
        severity: "critical",
        type: "high_abandonment",
        message: "High abandonment rate",
        value: Math.round((row.abandoned / row.started) * 100),
        threshold: 50
      });
    }

    // Critical: Survey stalled (no responses in 7 days but still published)
    if (row.status === "published" && row.last_completed_at) {
      const daysSinceLastResponse = (now.getTime() - new Date(row.last_completed_at).getTime()) / (1000 * 60 * 60 * 24);
      if (daysSinceLastResponse > 7 && row.reach > 0) {
        alerts.push({
          surveyId: row.id,
          surveyTitle: row.title,
          severity: "critical",
          type: "stalled_survey",
          message: "Survey stalled - no recent responses",
          value: Math.round(daysSinceLastResponse),
          threshold: 7
        });
      }
    }

    // Warning: Below average response rate (20-40%)
    if (row.status === "published" && row.response_rate !== null && row.response_rate >= 0.2 && row.response_rate < 0.4) {
      alerts.push({
        surveyId: row.id,
        surveyTitle: row.title,
        severity: "warning",
        type: "below_average_response",
        message: "Below average response rate",
        value: Math.round(row.response_rate * 100),
        threshold: 40
      });
    }

    // Warning: Aging survey (published > 14 days ago, not closed)
    if (row.status === "published" && row.closed_at === null) {
      const daysSincePublished = (now.getTime() - new Date(row.updated_at).getTime()) / (1000 * 60 * 60 * 24);
      if (daysSincePublished > 14) {
        alerts.push({
          surveyId: row.id,
          surveyTitle: row.title,
          severity: "warning",
          type: "aging_survey",
          message: "Survey aging - consider closing",
          value: Math.round(daysSincePublished),
          threshold: 14
        });
      }
    }

    // Warning: High in-progress count (many people started but not finished)
    if (row.in_progress > 5 && row.completed > 0) {
      const inProgressRatio = row.in_progress / row.completed;
      if (inProgressRatio > 0.3) {
        alerts.push({
          surveyId: row.id,
          surveyTitle: row.title,
          severity: "warning",
          type: "high_in_progress",
          message: "Many incomplete responses",
          value: row.in_progress,
          threshold: 5
        });
      }
    }

    // Info: New survey (published < 3 days ago)
    if (row.status === "published") {
      const daysSincePublished = (now.getTime() - new Date(row.updated_at).getTime()) / (1000 * 60 * 60 * 24);
      if (daysSincePublished < 3) {
        alerts.push({
          surveyId: row.id,
          surveyTitle: row.title,
          severity: "info",
          type: "new_survey",
          message: "Recently published",
          value: Math.round(daysSincePublished),
          threshold: 3
        });
      }
    }

    // Success: Excellent response rate (> 80%)
    if (row.status === "published" && row.response_rate !== null && row.response_rate > 0.8) {
      alerts.push({
        surveyId: row.id,
        surveyTitle: row.title,
        severity: "success",
        type: "excellent_response",
        message: "Excellent response rate",
        value: Math.round(row.response_rate * 100),
        threshold: 80
      });
    }
  }

  return alerts;
}

/**
 * Calculate response velocity (responses per day since publication)
 */
export function calculateResponseVelocity(row: DashboardRow): number | null {
  if (row.status !== "published" || row.completed === 0) return null;
  
  const now = new Date();
  const publishedDate = new Date(row.updated_at);
  const daysSincePublished = Math.max(1, (now.getTime() - publishedDate.getTime()) / (1000 * 60 * 60 * 24));
  
  return row.completed / daysSincePublished;
}

/**
 * Detect unusually slow response velocity
 */
export function detectSlowVelocity(rows: DashboardRow[]): SurveyAlert[] {
  const alerts: SurveyAlert[] = [];
  
  // Calculate average velocity across all published surveys
  const publishedRows = rows.filter(r => r.status === "published");
  const velocities = publishedRows
    .map(calculateResponseVelocity)
    .filter((v): v is number => v !== null);
  
  if (velocities.length === 0) return alerts;
  
  const avgVelocity = velocities.reduce((sum, v) => sum + v, 0) / velocities.length;
  
  for (const row of publishedRows) {
    const velocity = calculateResponseVelocity(row);
    if (velocity !== null && velocity < avgVelocity * 0.5) {
      alerts.push({
        surveyId: row.id,
        surveyTitle: row.title,
        severity: "warning",
        type: "slow_velocity",
        message: "Unusually slow response rate",
        value: Math.round(velocity * 10) / 10,
        threshold: Math.round(avgVelocity * 0.5 * 10) / 10
      });
    }
  }
  
  return alerts;
}

/**
 * Predict if survey will meet completion target
 */
export function predictCompletionTarget(row: DashboardRow, targetRate: number = 0.7): {
  willMeetTarget: boolean;
  projectedRate: number;
  daysNeeded: number | null;
} {
  if (row.status !== "published" || row.response_rate === null) {
    return { willMeetTarget: false, projectedRate: 0, daysNeeded: null };
  }
  
  const currentRate = row.response_rate;
  const completed = row.completed;
  const started = row.started;
  const reach = row.reach;
  
  if (started === 0 || reach === 0) {
    return { willMeetTarget: false, projectedRate: currentRate, daysNeeded: null };
  }
  
  // Calculate current velocity
  const now = new Date();
  const publishedDate = new Date(row.updated_at);
  const daysSincePublished = Math.max(1, (now.getTime() - publishedDate.getTime()) / (1000 * 60 * 60 * 24));
  const velocity = completed / daysSincePublished;
  
  // Project completion
  const remainingToReach = reach - completed;
  const daysNeeded = velocity > 0 ? remainingToReach / velocity : null;
  
  // Projected rate based on current trajectory
  const projectedTotalResponses = completed + (velocity * daysSincePublished);
  const projectedRate = reach > 0 ? projectedTotalResponses / reach : currentRate;
  
  return {
    willMeetTarget: projectedRate >= targetRate,
    projectedRate,
    daysNeeded
  };
}