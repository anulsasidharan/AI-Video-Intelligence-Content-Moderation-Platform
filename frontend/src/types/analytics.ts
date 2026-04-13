import type { ViolationCategory } from './moderation';

// Matches backend app/schemas/analytics.py → AnalyticsSummary
export interface AnalyticsSummary {
  total_videos_processed: number;
  total_violations_detected: number;
  violation_rate_percent: number; // 0–100
  avg_confidence: number;
  videos_approved: number;
  videos_rejected: number;
  videos_escalated: number;
  top_violation_categories: { category: string; count: number }[];
}

// Matches backend ViolationDataPoint
export interface ViolationDataPoint {
  date: string;
  count: number;
  category?: ViolationCategory;
}

// Matches backend ViolationBreakdown
export interface ViolationBreakdown {
  category: string;
  count: number;
  percentage: number;
}

// Matches backend ViolationsResponse (flat, no data wrapper)
export interface ViolationsResponse {
  time_series: ViolationDataPoint[];
  breakdown: ViolationBreakdown[];
  total: number;
  date_from: string;
  date_to: string;
}

// Kept for backward compatibility (not used in hooks)
export interface AnalyticsSummaryResponse {
  data: AnalyticsSummary;
}

export interface AnalyticsParams {
  from?: string;
  to?: string;
  tenant_id?: string;
}

export interface ViolationsParams extends AnalyticsParams {
  policy_id?: string;
  category?: ViolationCategory;
}
