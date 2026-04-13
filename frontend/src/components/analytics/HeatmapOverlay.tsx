'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { VIOLATION_CATEGORY_LABELS } from '@/lib/constants';
import type { ViolationBreakdown } from '@/types/analytics';

interface HeatmapOverlayProps {
  data?: ViolationBreakdown[];
  isLoading?: boolean;
  className?: string;
}

export function HeatmapOverlay({ data, isLoading, className }: HeatmapOverlayProps) {
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const maxCount = Math.max(...(data ?? []).map((d) => d.count), 1);

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-base">Violations by category</CardTitle>
      </CardHeader>
      <CardContent>
        {!data || data.length === 0 ? (
          <p className="text-sm text-muted-foreground">No violation data available.</p>
        ) : (
          <div className="space-y-3">
            {data.map((item) => {
              const intensity = item.count / maxCount;
              return (
                <div key={item.category} className="flex items-center gap-3">
                  <span className="w-28 shrink-0 text-xs text-muted-foreground">
                    {VIOLATION_CATEGORY_LABELS[item.category]}
                  </span>
                  <div className="flex-1 overflow-hidden rounded">
                    <div
                      className={cn(
                        'h-7 rounded transition-all',
                        intensity > 0.75
                          ? 'bg-destructive'
                          : intensity > 0.4
                          ? 'bg-yellow-500/80'
                          : 'bg-primary/60'
                      )}
                      style={{ width: `${Math.max(intensity * 100, 4)}%` }}
                      aria-label={`${VIOLATION_CATEGORY_LABELS[item.category]}: ${item.count}`}
                    />
                  </div>
                  <div className="w-24 text-right text-xs text-muted-foreground tabular-nums">
                    {item.count} ({item.percentage.toFixed(1)}%)
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
