'use client';

import { useEffect, useRef } from 'react';
import { AlertTriangle, Baby, Eye, FileText, ShieldCheck, ShieldX } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { formatDistanceToNow } from 'date-fns';

export interface LiveEvent {
  id: string; // client-side UUID for keying
  timestamp: Date;
  event: string;
  overall_safe?: boolean;
  requires_immediate_action?: boolean;
  highest_severity?: string | null;
  violations?: Array<{
    category: string;
    severity: string;
    confidence: number;
    description: string;
  }>;
  face_analysis?: {
    face_count: number;
    has_minor: boolean;
    restricted_content: boolean;
    liveness_score: number;
    summary: string;
  };
  ocr_text?: string;
  content_summary?: string;
}

interface LiveAlertFeedProps {
  events: LiveEvent[];
  maxHeight?: string;
}

const severityColors: Record<string, string> = {
  critical: 'bg-red-100 border-red-400 text-red-900 dark:bg-red-900/30 dark:border-red-600',
  high:     'bg-orange-100 border-orange-400 text-orange-900 dark:bg-orange-900/30 dark:border-orange-600',
  medium:   'bg-yellow-100 border-yellow-400 text-yellow-900 dark:bg-yellow-900/30 dark:border-yellow-600',
  low:      'bg-blue-100 border-blue-400 text-blue-900 dark:bg-blue-900/30 dark:border-blue-600',
};

const severityBadge: Record<string, 'destructive' | 'warning' | 'secondary'> = {
  critical: 'destructive',
  high:     'destructive',
  medium:   'warning',
  low:      'secondary',
};

export function LiveAlertFeed({ events, maxHeight = '480px' }: LiveAlertFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest event
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events.length]);

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        <ShieldCheck className="mb-2 h-8 w-8 text-green-500" />
        <p className="text-sm font-medium">All clear</p>
        <p className="text-xs mt-1">No moderation events yet. Start capture to begin analysis.</p>
      </div>
    );
  }

  return (
    <ScrollArea style={{ maxHeight }} className="rounded-lg border">
      <div className="space-y-2 p-3">
        {events.map((evt) => (
          <EventCard key={evt.id} event={evt} />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}

function EventCard({ event }: { event: LiveEvent }) {
  // System events (moderation start/stop)
  if (event.event === 'moderation.started') {
    return (
      <div className="flex items-center gap-2 rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 px-3 py-2 text-sm text-green-800 dark:text-green-200">
        <ShieldCheck className="h-4 w-4 shrink-0" />
        <span>Moderation started</span>
        <span className="ml-auto text-xs opacity-60">
          {formatDistanceToNow(event.timestamp, { addSuffix: true })}
        </span>
      </div>
    );
  }

  if (event.event === 'moderation.stopped' || event.event === 'stream.stopped') {
    return (
      <div className="flex items-center gap-2 rounded-md bg-slate-50 dark:bg-slate-900/20 border border-slate-200 dark:border-slate-700 px-3 py-2 text-sm text-slate-600 dark:text-slate-400">
        <ShieldX className="h-4 w-4 shrink-0" />
        <span>{event.event === 'stream.stopped' ? 'Stream stopped' : 'Moderation stopped'}</span>
        <span className="ml-auto text-xs opacity-60">
          {formatDistanceToNow(event.timestamp, { addSuffix: true })}
        </span>
      </div>
    );
  }

  // Frame moderation result
  if (event.event === 'frame.moderated') {
    const hasFaceIssue = event.face_analysis?.has_minor || event.face_analysis?.restricted_content;
    const hasViolations = (event.violations?.length ?? 0) > 0;

    if (event.overall_safe && !hasFaceIssue) {
      return (
        <div className="flex items-center gap-2 rounded-md bg-muted/40 border px-3 py-2 text-xs text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5 shrink-0 text-green-500" />
          <span>Frame analysed — all clear</span>
          {event.content_summary && (
            <span className="truncate max-w-[200px] opacity-70">{event.content_summary}</span>
          )}
          <span className="ml-auto shrink-0">
            {formatDistanceToNow(event.timestamp, { addSuffix: true })}
          </span>
        </div>
      );
    }

    const topSeverity = event.highest_severity ?? 'medium';
    const colorClass = severityColors[topSeverity] ?? severityColors.medium;

    return (
      <div className={`rounded-md border px-3 py-2 space-y-2 text-sm ${colorClass}`}>
        {/* Header */}
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span className="font-semibold">
            {event.requires_immediate_action ? 'Immediate action required' : 'Violation detected'}
          </span>
          <Badge
            variant={severityBadge[topSeverity] ?? 'secondary'}
            className="ml-auto text-xs"
          >
            {topSeverity.toUpperCase()}
          </Badge>
          <span className="text-xs opacity-60 shrink-0">
            {formatDistanceToNow(event.timestamp, { addSuffix: true })}
          </span>
        </div>

        {/* Violations list */}
        {hasViolations && (
          <ul className="space-y-1">
            {event.violations!.map((v, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs">
                <AlertTriangle className="h-3 w-3 mt-0.5 shrink-0" />
                <span>
                  <span className="font-medium capitalize">{v.category.replace(/_/g, ' ')}</span>
                  {' — '}{v.description}
                  <span className="opacity-60 ml-1">({Math.round(v.confidence * 100)}%)</span>
                </span>
              </li>
            ))}
          </ul>
        )}

        {/* Face analysis */}
        {hasFaceIssue && (
          <div className="flex items-center gap-1.5 text-xs bg-black/10 rounded px-2 py-1">
            <Baby className="h-3 w-3 shrink-0" />
            <span>
              {event.face_analysis!.has_minor
                ? 'Minor detected — age-restricted content may be inappropriate'
                : 'Restricted content flag'}
              {event.face_analysis!.summary && ` — ${event.face_analysis!.summary}`}
            </span>
          </div>
        )}

        {/* OCR text */}
        {event.ocr_text && event.ocr_text.length > 0 && (
          <div className="flex items-start gap-1.5 text-xs opacity-80">
            <FileText className="h-3 w-3 mt-0.5 shrink-0" />
            <span className="line-clamp-2">{event.ocr_text}</span>
          </div>
        )}

        {/* Liveness */}
        {event.face_analysis && event.face_analysis.liveness_score < 0.6 && (
          <div className="flex items-center gap-1.5 text-xs opacity-80">
            <Eye className="h-3 w-3 shrink-0" />
            <span>
              Low liveness score ({Math.round(event.face_analysis.liveness_score * 100)}%) —
              face may be a photo or screen
            </span>
          </div>
        )}
      </div>
    );
  }

  return null;
}
