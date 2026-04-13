'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

// ── Types ──────────────────────────────────────────────────────────────────────

export type NotificationChannel = 'email' | 'in_app' | 'whatsapp';
export type NotificationStatus = 'pending' | 'sent' | 'failed' | 'read';
export type NotificationPriority = 'low' | 'medium' | 'high' | 'critical';
export type NotificationFrequency = 'instant' | 'batched' | 'daily_digest';

export interface AppNotification {
  id: string;
  user_id: string;
  channel: NotificationChannel;
  event_type: string;
  priority: NotificationPriority;
  title: string;
  message: string;
  data: Record<string, unknown> | null;
  status: NotificationStatus;
  scheduled_at: string | null;
  sent_at: string | null;
  read_at: string | null;
  retry_count: number;
  tenant_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationListResponse {
  items: AppNotification[];
  total: number;
  unread_count: number;
}

export interface NotificationPreferenceItem {
  id: string;
  channel: NotificationChannel;
  event_type: string;
  enabled: boolean;
  quiet_hours_start: number | null;
  quiet_hours_end: number | null;
  frequency: NotificationFrequency;
  updated_at: string;
}

export interface NotificationPreferencesResponse {
  items: NotificationPreferenceItem[];
  total: number;
}

export interface PreferenceUpsert {
  channel: NotificationChannel;
  event_type: string;
  enabled: boolean;
  quiet_hours_start?: number | null;
  quiet_hours_end?: number | null;
  frequency: NotificationFrequency;
}

// ── Query keys ────────────────────────────────────────────────────────────────

export const NOTIFICATION_KEYS = {
  all: ['notifications'] as const,
  list: (unreadOnly: boolean) => ['notifications', 'list', unreadOnly] as const,
  preferences: () => ['notifications', 'preferences'] as const,
  eventTypes: () => ['notifications', 'event-types'] as const,
};

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useNotifications(unreadOnly = false) {
  const queryClient = useQueryClient();

  // ── Queries ──────────────────────────────────────────────────────────────

  const notificationsQuery = useQuery<NotificationListResponse>({
    queryKey: NOTIFICATION_KEYS.list(unreadOnly),
    queryFn: () =>
      apiClient.get<NotificationListResponse>(
        `/notifications?unread_only=${unreadOnly}&limit=50`
      ),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  const preferencesQuery = useQuery<NotificationPreferencesResponse>({
    queryKey: NOTIFICATION_KEYS.preferences(),
    queryFn: () =>
      apiClient.get<NotificationPreferencesResponse>('/notifications/preferences'),
  });

  const eventTypesQuery = useQuery<{ event_types: string[] }>({
    queryKey: NOTIFICATION_KEYS.eventTypes(),
    queryFn: () => apiClient.get<{ event_types: string[] }>('/notifications/event-types'),
    staleTime: Infinity,
  });

  // ── Mutations ─────────────────────────────────────────────────────────────

  const markReadMutation = useMutation({
    mutationFn: (notificationId: string) =>
      apiClient.patch(`/notifications/${notificationId}/read`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => apiClient.post('/notifications/read-all', {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (notificationId: string) =>
      apiClient.delete(`/notifications/${notificationId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
  });

  const updatePreferencesMutation = useMutation({
    mutationFn: (preferences: PreferenceUpsert[]) =>
      apiClient.put<NotificationPreferencesResponse>('/notifications/preferences', {
        preferences,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.preferences() });
    },
  });

  // ── Computed values ───────────────────────────────────────────────────────

  const notifications = notificationsQuery.data?.items ?? [];
  const unreadCount = notificationsQuery.data?.unread_count ?? 0;
  const preferences = preferencesQuery.data?.items ?? [];
  const eventTypes = eventTypesQuery.data?.event_types ?? [];

  return {
    // Data
    notifications,
    unreadCount,
    preferences,
    eventTypes,
    // Loading states
    isLoading: notificationsQuery.isLoading,
    isPreferencesLoading: preferencesQuery.isLoading,
    // Actions
    markRead: markReadMutation.mutate,
    markAllRead: markAllReadMutation.mutate,
    deleteNotification: deleteMutation.mutate,
    updatePreferences: updatePreferencesMutation.mutate,
    // Mutation states
    isMarkingRead: markReadMutation.isPending,
    isMarkingAllRead: markAllReadMutation.isPending,
    isUpdatingPreferences: updatePreferencesMutation.isPending,
  };
}
