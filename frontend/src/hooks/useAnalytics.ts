'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type {
  AnalyticsSummary,
  ViolationsResponse,
  AnalyticsParams,
  ViolationsParams,
} from '@/types/analytics';

export const analyticsKeys = {
  summary: (params: AnalyticsParams) => ['analytics', 'summary', params] as const,
  violations: (params: ViolationsParams) => ['analytics', 'violations', params] as const,
};

export function useAnalyticsSummary(params: AnalyticsParams = {}) {
  return useQuery({
    queryKey: analyticsKeys.summary(params),
    // apiClient.get already unwraps the { data: ... } envelope, so the
    // resolved type is AnalyticsSummary, not AnalyticsSummaryResponse.
    queryFn: () =>
      apiClient.get<AnalyticsSummary>('/analytics/summary', { params }),
    staleTime: 5 * 60 * 1000,
  });
}

export function useViolationsData(params: ViolationsParams = {}) {
  return useQuery({
    queryKey: analyticsKeys.violations(params),
    // Same unwrapping — the payload is the inner data shape, not the wrapper.
    queryFn: () =>
      apiClient.get<ViolationsResponse>('/analytics/violations', { params }),
    staleTime: 5 * 60 * 1000,
  });
}
