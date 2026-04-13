'use client';

import { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { VIOLATION_CATEGORY_LABELS } from '@/lib/constants';
import type { Violation } from '@/types/moderation';

interface TimelineAnnotationProps {
  violations: Violation[];
  duration: number;
  currentTime: number;
  onSeek: (seconds: number) => void;
  className?: string;
}

const categoryColors: Record<string, string> = {
  violence: 'bg-red-500',
  nudity: 'bg-pink-500',
  drugs: 'bg-purple-500',
  hate_symbols: 'bg-orange-500',
  spam: 'bg-yellow-500',
  misinformation: 'bg-blue-500',
  other: 'bg-gray-500',
};

export function TimelineAnnotation({
  violations,
  duration,
  currentTime,
  onSeek,
  className,
}: TimelineAnnotationProps) {
  const markers = useMemo(
    () =>
      violations
        .filter((v) => v.timestamp_seconds !== undefined)
        .map((v) => ({
          ...v,
          position: ((v.timestamp_seconds ?? 0) / duration) * 100,
        })),
    [violations, duration]
  );

  const playheadPosition = (currentTime / duration) * 100;

  if (duration <= 0) return null;

  return (
    <div className={cn('relative h-8 w-full', className)}>
      {/* Track */}
      <div
        className="absolute inset-x-0 top-3 h-2 cursor-pointer rounded-full bg-muted"
        onClick={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const ratio = Math.max(0, Math.min(1, x / rect.width));
          onSeek(ratio * duration);
        }}
        role="slider"
        aria-label="Video timeline"
        aria-valuenow={currentTime}
        aria-valuemin={0}
        aria-valuemax={duration}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'ArrowLeft') onSeek(Math.max(0, currentTime - 5));
          if (e.key === 'ArrowRight') onSeek(Math.min(duration, currentTime + 5));
        }}
      >
        {/* Violation markers */}
        {markers.map((marker) => (
          <button
            key={marker.id}
            className={cn(
              'absolute top-1/2 h-4 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full transition-opacity hover:opacity-100',
              categoryColors[marker.category] ?? 'bg-gray-500'
            )}
            style={{ left: `${marker.position}%` }}
            onClick={(e) => {
              e.stopPropagation();
              onSeek(marker.timestamp_seconds ?? 0);
            }}
            title={`${VIOLATION_CATEGORY_LABELS[marker.category]} — ${Math.round(marker.confidence * 100)}% confidence`}
            aria-label={`Jump to ${VIOLATION_CATEGORY_LABELS[marker.category]} violation`}
          />
        ))}

        {/* Playhead */}
        <div
          className="absolute top-1/2 h-4 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary"
          style={{ left: `${playheadPosition}%` }}
        />
      </div>

      {/* Legend */}
      {markers.length > 0 && (
        <div className="absolute right-0 top-0 flex gap-2">
          {[...new Set(markers.map((m) => m.category))].map((cat) => (
            <span key={cat} className="flex items-center gap-1 text-xs text-muted-foreground">
              <span className={cn('h-2 w-2 rounded-full', categoryColors[cat])} />
              {VIOLATION_CATEGORY_LABELS[cat]}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
