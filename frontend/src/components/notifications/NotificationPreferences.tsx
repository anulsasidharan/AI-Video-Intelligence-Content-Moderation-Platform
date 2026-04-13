'use client';

import { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import {
  type NotificationChannel,
  type NotificationFrequency,
  type PreferenceUpsert,
  useNotifications,
} from '@/hooks/useNotifications';

// ── Constants ─────────────────────────────────────────────────────────────────

const CHANNELS: { value: NotificationChannel; label: string; description: string }[] = [
  { value: 'in_app', label: 'In-App', description: 'Real-time alerts in the dashboard' },
  { value: 'email', label: 'Email', description: 'Delivered to your registered email' },
  { value: 'whatsapp', label: 'WhatsApp', description: 'Critical alerts to your phone' },
];

const FREQUENCIES: { value: NotificationFrequency; label: string }[] = [
  { value: 'instant', label: 'Instant' },
  { value: 'batched', label: 'Batched' },
  { value: 'daily_digest', label: 'Daily digest' },
];

const EVENT_LABELS: Record<string, string> = {
  'video.uploaded': 'Video Uploaded',
  'moderation.complete': 'Moderation Complete',
  'moderation.flagged': 'Content Flagged',
  'policy.violation': 'Policy Violation',
  'stream.alert': 'Live Stream Alert',
  'batch.complete': 'Batch Processing Complete',
  'system.quota_warning': 'Quota Warning',
  'system.api_error': 'API Error',
};

// ── Types ──────────────────────────────────────────────────────────────────────

interface PrefKey {
  channel: NotificationChannel;
  event_type: string;
}

type PrefMap = Record<string, PreferenceUpsert>;

function prefKey(channel: NotificationChannel, event_type: string): string {
  return `${channel}::${event_type}`;
}

// ── Component ──────────────────────────────────────────────────────────────────

export function NotificationPreferences() {
  const {
    preferences,
    eventTypes,
    isPreferencesLoading,
    updatePreferences,
    isUpdatingPreferences,
  } = useNotifications();

  // Local editable state
  const [localPrefs, setLocalPrefs] = useState<PrefMap>({});
  const [isDirty, setIsDirty] = useState(false);

  // Initialise local state from fetched preferences
  useEffect(() => {
    if (preferences.length > 0 || eventTypes.length > 0) {
      const map: PrefMap = {};

      // Seed with server values
      for (const pref of preferences) {
        map[prefKey(pref.channel, pref.event_type)] = {
          channel: pref.channel,
          event_type: pref.event_type,
          enabled: pref.enabled,
          quiet_hours_start: pref.quiet_hours_start,
          quiet_hours_end: pref.quiet_hours_end,
          frequency: pref.frequency,
        };
      }

      // Seed defaults for any channel/event combo not yet stored
      for (const channel of CHANNELS.map((c) => c.value)) {
        for (const event_type of eventTypes) {
          const k = prefKey(channel, event_type);
          if (!map[k]) {
            map[k] = {
              channel,
              event_type,
              enabled: channel === 'in_app', // in_app on by default
              quiet_hours_start: null,
              quiet_hours_end: null,
              frequency: 'instant',
            };
          }
        }
      }

      setLocalPrefs(map);
      setIsDirty(false);
    }
  }, [preferences, eventTypes]);

  function setPref(
    channel: NotificationChannel,
    event_type: string,
    patch: Partial<PreferenceUpsert>
  ) {
    const k = prefKey(channel, event_type);
    setLocalPrefs((prev) => ({
      ...prev,
      [k]: { ...prev[k], ...patch },
    }));
    setIsDirty(true);
  }

  function handleSave() {
    updatePreferences(Object.values(localPrefs));
    setIsDirty(false);
  }

  if (isPreferencesLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Notification Preferences</CardTitle>
            <CardDescription className="mt-1">
              Configure which channels receive each event type and when.
            </CardDescription>
          </div>
          <Button
            onClick={handleSave}
            disabled={!isDirty || isUpdatingPreferences}
            size="sm"
          >
            {isUpdatingPreferences ? 'Saving…' : 'Save changes'}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {/* Channel sections */}
        {CHANNELS.map((channel, cidx) => (
          <div key={channel.value}>
            {cidx > 0 && <Separator />}
            <div className="px-6 py-4">
              {/* Channel header */}
              <div className="mb-4 flex items-center gap-2">
                <h3 className="text-sm font-semibold">{channel.label}</h3>
                <Badge variant="outline" className="text-[10px]">
                  {channel.description}
                </Badge>
              </div>

              {/* Event rows */}
              <div className="space-y-3">
                {eventTypes.map((event_type) => {
                  const k = prefKey(channel.value, event_type);
                  const pref = localPrefs[k];
                  if (!pref) return null;

                  return (
                    <div
                      key={event_type}
                      className="flex flex-col gap-2 rounded-md border border-border/40 p-3 sm:flex-row sm:items-center sm:justify-between"
                    >
                      {/* Label + toggle */}
                      <div className="flex items-center gap-3">
                        <Switch
                          id={`${k}-enabled`}
                          checked={pref.enabled}
                          onCheckedChange={(checked) =>
                            setPref(channel.value, event_type, { enabled: checked })
                          }
                        />
                        <Label
                          htmlFor={`${k}-enabled`}
                          className="cursor-pointer text-sm"
                        >
                          {EVENT_LABELS[event_type] ?? event_type}
                        </Label>
                      </div>

                      {/* Frequency selector — only visible when enabled */}
                      {pref.enabled && (
                        <div className="flex items-center gap-2 pl-9 sm:pl-0">
                          <span className="text-xs text-muted-foreground">Frequency</span>
                          <Select
                            value={pref.frequency}
                            onValueChange={(v) =>
                              setPref(channel.value, event_type, {
                                frequency: v as NotificationFrequency,
                              })
                            }
                          >
                            <SelectTrigger className="h-7 w-32 text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {FREQUENCIES.map((f) => (
                                <SelectItem key={f.value} value={f.value} className="text-xs">
                                  {f.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ))}

        {/* Quiet hours section */}
        <Separator />
        <div className="px-6 py-4">
          <div className="mb-3">
            <h3 className="text-sm font-semibold">Quiet Hours</h3>
            <p className="text-xs text-muted-foreground mt-1">
              Notifications will be deferred outside this window (UTC). Applies to all channels.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Label className="text-xs text-muted-foreground">From</Label>
              <Select
                value={
                  Object.values(localPrefs)[0]?.quiet_hours_start?.toString() ?? 'none'
                }
                onValueChange={(v) => {
                  const hour = v === 'none' ? null : parseInt(v, 10);
                  setLocalPrefs((prev) => {
                    const next = { ...prev };
                    for (const k of Object.keys(next)) {
                      next[k] = { ...next[k], quiet_hours_start: hour };
                    }
                    return next;
                  });
                  setIsDirty(true);
                }}
              >
                <SelectTrigger className="h-7 w-24 text-xs">
                  <SelectValue placeholder="Off" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none" className="text-xs">Off</SelectItem>
                  {Array.from({ length: 24 }, (_, i) => (
                    <SelectItem key={i} value={i.toString()} className="text-xs">
                      {String(i).padStart(2, '0')}:00
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Label className="text-xs text-muted-foreground">To</Label>
              <Select
                value={
                  Object.values(localPrefs)[0]?.quiet_hours_end?.toString() ?? 'none'
                }
                onValueChange={(v) => {
                  const hour = v === 'none' ? null : parseInt(v, 10);
                  setLocalPrefs((prev) => {
                    const next = { ...prev };
                    for (const k of Object.keys(next)) {
                      next[k] = { ...next[k], quiet_hours_end: hour };
                    }
                    return next;
                  });
                  setIsDirty(true);
                }}
              >
                <SelectTrigger className="h-7 w-24 text-xs">
                  <SelectValue placeholder="Off" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none" className="text-xs">Off</SelectItem>
                  {Array.from({ length: 24 }, (_, i) => (
                    <SelectItem key={i} value={i.toString()} className="text-xs">
                      {String(i).padStart(2, '0')}:00
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
