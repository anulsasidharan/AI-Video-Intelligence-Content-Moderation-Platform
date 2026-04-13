'use client';

import { X, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useShallow } from 'zustand/react/shallow';
import { useModerationStore, selectUndismissedAlerts } from '@/stores/moderationStore';
import { formatDistanceToNow } from 'date-fns';
import { VIOLATION_CATEGORY_LABELS } from '@/lib/constants';

export function AlertBanner() {
  const alerts = useModerationStore(useShallow(selectUndismissedAlerts));
  const { dismissAlert } = useModerationStore();

  if (alerts.length === 0) return null;

  return (
    <div className="border-b border-destructive/30 bg-destructive/10" role="alert" aria-live="polite">
      <div className="space-y-1 p-2">
        {alerts.slice(0, 3).map((alert) => (
          <div
            key={alert.id}
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm"
          >
            <AlertTriangle className="h-4 w-4 shrink-0 text-destructive" />
            <div className="flex flex-1 items-center gap-2 min-w-0">
              <Badge variant="destructive" className="text-xs shrink-0">
                {VIOLATION_CATEGORY_LABELS[alert.category] ?? alert.category}
              </Badge>
              {alert.stream_id && (
                <span className="text-xs text-muted-foreground truncate">
                  Stream {alert.stream_id.slice(0, 8)}
                </span>
              )}
              <span className="text-xs text-muted-foreground shrink-0">
                {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
              </span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 shrink-0"
              onClick={() => dismissAlert(alert.id)}
              aria-label="Dismiss alert"
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        ))}
        {alerts.length > 3 && (
          <p className="px-3 text-xs text-muted-foreground">
            +{alerts.length - 3} more alert{alerts.length - 3 !== 1 ? 's' : ''}
          </p>
        )}
      </div>
    </div>
  );
}
