'use client';

import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { formatPercent } from '@/lib/utils';
import { VIOLATION_CATEGORY_LABELS } from '@/lib/constants';
import type { Violation } from '@/types/moderation';

interface FrameInspectorProps {
  currentTime: number;
  violations: Violation[];
  isLoading?: boolean;
  className?: string;
}

export function FrameInspector({
  currentTime,
  violations,
  isLoading,
  className,
}: FrameInspectorProps) {
  // Find violations near the current timestamp (±2 seconds)
  const nearbyViolations = violations.filter(
    (v) =>
      v.timestamp_seconds !== undefined &&
      Math.abs(v.timestamp_seconds - currentTime) <= 2
  );

  return (
    <div className={`rounded-lg border bg-card p-4 ${className ?? ''}`}>
      <h3 className="mb-3 text-sm font-semibold">Frame Inspector</h3>
      <p className="mb-3 text-xs text-muted-foreground">
        t = {currentTime.toFixed(1)}s
      </p>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : nearbyViolations.length === 0 ? (
        <p className="text-xs text-muted-foreground">No detections at this timestamp.</p>
      ) : (
        <ScrollArea className="max-h-60">
          <ul className="space-y-2">
            {nearbyViolations.map((v) => (
              <li
                key={v.id}
                className="flex items-start gap-3 rounded-md border bg-muted/30 p-3"
              >
                {v.frame_url && (
                  <div className="relative h-12 w-20 shrink-0 overflow-hidden rounded">
                    <Image src={v.frame_url} alt="Frame" fill className="object-cover" />
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="destructive" className="text-xs">
                      {VIOLATION_CATEGORY_LABELS[v.category]}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {formatPercent(v.confidence)} confidence
                    </span>
                  </div>
                  {v.snippet && (
                    <p className="mt-1 truncate text-xs text-muted-foreground">
                      {v.snippet}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </ScrollArea>
      )}
    </div>
  );
}
