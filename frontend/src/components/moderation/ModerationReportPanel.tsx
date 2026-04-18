'use client';

import { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Download,
  FileText,
  ShieldAlert,
  ShieldCheck,
  Zap,
  Lock,
  UserCheck,
  Trash2,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn, formatDuration } from '@/lib/utils';
import { AgentActivityLog } from '@/components/video/AgentActivityLog';
import type { AgentLogEntry } from '@/components/video/AgentActivityLog';
import type { ModerationQueueItem, AiViolation } from '@/types/moderation';

// ── Severity helpers ──────────────────────────────────────────────────────────

const SEVERITY_STYLES = {
  high: {
    badge: 'bg-red-900/40 text-red-400 border-red-700/50',
    bar: 'bg-red-500',
    ring: 'border-red-500/30 bg-red-950/20',
    dot: 'bg-red-500',
  },
  medium: {
    badge: 'bg-yellow-900/40 text-yellow-400 border-yellow-700/50',
    bar: 'bg-yellow-500',
    ring: 'border-yellow-500/30 bg-yellow-950/20',
    dot: 'bg-yellow-500',
  },
  low: {
    badge: 'bg-slate-800 text-slate-400 border-slate-600',
    bar: 'bg-slate-400',
    ring: 'border-slate-600 bg-slate-900',
    dot: 'bg-slate-400',
  },
  critical: {
    badge: 'bg-red-900/60 text-red-300 border-red-600',
    bar: 'bg-red-400',
    ring: 'border-red-400/40 bg-red-950/30',
    dot: 'bg-red-400',
  },
};

const CATEGORY_LABELS: Record<string, string> = {
  violence: 'Violence',
  nudity: 'Explicit Content',
  drugs: 'Weapon / Threat',
  hate_symbols: 'Threatening Language',
  spam: 'Spam',
  misinformation: 'Misinformation',
  other: 'Other',
};

// ── Verdict header ────────────────────────────────────────────────────────────

function VerdictHeader({
  status,
  confidence,
  processingTime,
  policy,
}: {
  status: string;
  confidence: number;
  processingTime: string;
  policy: string;
}) {
  const isFlagged = status === 'flagged' || status === 'rejected';

  return (
    <div className={cn(
      'rounded-xl border p-5 flex flex-col sm:flex-row sm:items-center gap-4',
      isFlagged ? 'border-red-500/30 bg-red-950/10' : 'border-green-500/30 bg-green-950/10',
    )}>
      <div className={cn(
        'w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0',
        isFlagged ? 'bg-red-500/15' : 'bg-green-500/15',
      )}>
        {isFlagged
          ? <ShieldAlert className="w-6 h-6 text-red-400" />
          : <ShieldCheck className="w-6 h-6 text-green-400" />
        }
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <span className={cn(
            'text-lg font-bold',
            isFlagged ? 'text-red-400' : 'text-green-400',
          )}>
            {isFlagged ? 'FLAGGED — REVIEW REQUIRED' : 'APPROVED'}
          </span>
          <span className={cn(
            'text-xs font-bold px-2 py-0.5 rounded-full border',
            isFlagged ? SEVERITY_STYLES.high.badge : 'bg-green-900/40 text-green-400 border-green-700/50',
          )}>
            {isFlagged ? 'HIGH' : 'CLEAN'}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">
          Policy: {policy} · Processing time: {processingTime}
        </p>
      </div>

      <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
        <div className="flex items-center gap-1.5">
          <Zap className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">AI Confidence</span>
        </div>
        <span className={cn(
          'text-2xl font-bold tabular-nums',
          isFlagged ? 'text-red-400' : 'text-green-400',
        )}>
          {Math.round(confidence * 100)}%
        </span>
      </div>
    </div>
  );
}

// ── Violation card ────────────────────────────────────────────────────────────

function ViolationDetailCard({ v, index }: { v: AiViolation; index: number }) {
  const styles = SEVERITY_STYLES[v.severity] ?? SEVERITY_STYLES.medium;
  const confPct = Math.round(v.confidence * 100);

  return (
    <div
      className={cn('rounded-xl border p-4 space-y-3', styles.ring)}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="flex items-center justify-between gap-2">
        <span className={cn('text-xs font-bold px-2 py-0.5 rounded-full border', styles.badge)}>
          {v.severity.toUpperCase()}
        </span>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="w-3 h-3" />
          {formatDuration(v.timestamp)}
        </div>
      </div>

      <div>
        <p className="text-sm font-semibold text-foreground">
          {CATEGORY_LABELS[v.category] ?? v.category}
        </p>
        <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
          {v.description}
        </p>
      </div>

      <div>
        <div className="flex justify-between text-xs mb-1.5">
          <span className="text-muted-foreground">Confidence</span>
          <span className="font-semibold tabular-nums">{confPct}%</span>
        </div>
        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
          <div
            className={cn('h-full rounded-full transition-all duration-1000', styles.bar)}
            style={{ width: `${confPct}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// ── Violation timeline ────────────────────────────────────────────────────────

function ViolationTimeline({
  violations,
  videoDuration = 754,
  onSeek,
}: {
  violations: AiViolation[];
  videoDuration?: number;
  onSeek?: (ts: number) => void;
}) {
  const [tooltip, setTooltip] = useState<number | null>(null);

  return (
    <div className="rounded-xl border bg-card p-4 space-y-3">
      <h4 className="text-sm font-medium">Violation Timeline</h4>
      <p className="text-xs text-muted-foreground">
        Click a marker to jump to that timestamp
      </p>

      <div className="relative h-8 flex items-center">
        {/* Track */}
        <div className="absolute inset-x-0 h-2 rounded-full bg-muted overflow-hidden">
          <div className="h-full w-full bg-gradient-to-r from-green-900/40 to-muted rounded-full" />
        </div>

        {/* Markers */}
        {violations.map((v, i) => {
          const pct = Math.min((v.timestamp / videoDuration) * 100, 100);
          const styles = SEVERITY_STYLES[v.severity] ?? SEVERITY_STYLES.medium;
          return (
            <button
              key={i}
              className="absolute -translate-x-1/2 flex flex-col items-center group cursor-pointer"
              style={{ left: `${pct}%` }}
              onClick={() => onSeek?.(v.timestamp)}
              onMouseEnter={() => setTooltip(i)}
              onMouseLeave={() => setTooltip(null)}
              aria-label={`${CATEGORY_LABELS[v.category]} at ${formatDuration(v.timestamp)}`}
            >
              <div className={cn(
                'w-4 h-4 rounded-full border-2 border-background shadow-lg transition-transform group-hover:scale-125',
                styles.dot,
              )} />

              {/* Tooltip */}
              {tooltip === i && (
                <div className="absolute bottom-6 z-10 whitespace-nowrap rounded-md bg-popover border shadow-lg px-2.5 py-1.5 text-xs pointer-events-none">
                  <span className="font-semibold">{CATEGORY_LABELS[v.category]}</span>
                  <span className="text-muted-foreground ml-1.5">@ {formatDuration(v.timestamp)}</span>
                  <br />
                  <span className="text-muted-foreground">Confidence: {Math.round(v.confidence * 100)}%</span>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 pt-1">
        {violations.map((v, i) => (
          <button
            key={i}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            onClick={() => onSeek?.(v.timestamp)}
          >
            <div className={cn('w-2 h-2 rounded-full', (SEVERITY_STYLES[v.severity] ?? SEVERITY_STYLES.medium).dot)} />
            {formatDuration(v.timestamp)} — {CATEGORY_LABELS[v.category]}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Action buttons panel ──────────────────────────────────────────────────────

function ActionPanel({ videoId }: { videoId: string }) {
  const [decision, setDecision] = useState<string | null>(null);

  const apply = (action: string, label: string) => {
    setDecision(action);
    toast.success(`Action applied: ${label}`, {
      description: `Video ${videoId} — logged in audit trail`,
    });
  };

  return (
    <div className="rounded-xl border bg-card p-4 space-y-3">
      <h4 className="text-sm font-medium">Policy Actions</h4>

      <div className="grid grid-cols-2 gap-2">
        <Button
          variant="destructive"
          size="sm"
          className="justify-start gap-2"
          disabled={!!decision}
          onClick={() => apply('quarantine', 'Quarantine')}
        >
          <Lock className="w-3.5 h-3.5" />
          Quarantine
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="justify-start gap-2 text-green-600 border-green-600/40 hover:bg-green-50 dark:hover:bg-green-950/20"
          disabled={!!decision}
          onClick={() => apply('approve', 'Approve')}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Override &amp; Approve
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="justify-start gap-2"
          disabled={!!decision}
          onClick={() => apply('escalate', 'Escalate to Human Review')}
        >
          <UserCheck className="w-3.5 h-3.5" />
          Escalate
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="justify-start gap-2 text-destructive border-destructive/40 hover:bg-destructive/10"
          disabled={!!decision}
          onClick={() => apply('delete', 'Delete Video')}
        >
          <Trash2 className="w-3.5 h-3.5" />
          Delete Video
        </Button>
      </div>

      {decision && (
        <p className="text-xs text-muted-foreground flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
          Action recorded in audit trail
        </p>
      )}

      <div className="border-t pt-3 flex flex-col gap-2">
        <Button
          variant="outline"
          size="sm"
          className="justify-start gap-2 w-full"
          onClick={() => toast.info('Generating PDF report…', { description: 'This would trigger a real download in production.' })}
        >
          <Download className="w-3.5 h-3.5" />
          Export PDF Report
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="justify-start gap-2 w-full"
          onClick={() => toast.info('Sending to review queue…')}
        >
          <FileText className="w-3.5 h-3.5" />
          Send to Reviewer Queue
        </Button>
      </div>
    </div>
  );
}

// ── Summary card ──────────────────────────────────────────────────────────────

function AiSummaryCard({ summary }: { summary: string }) {
  return (
    <div className="rounded-xl border bg-muted/30 p-4 space-y-2">
      <div className="flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-yellow-500 flex-shrink-0" />
        <h4 className="text-sm font-medium">AI Analysis Summary</h4>
      </div>
      <p className="text-sm text-muted-foreground leading-relaxed">{summary}</p>
    </div>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────────

interface ModerationReportPanelProps {
  result: ModerationQueueItem & {
    agent_log?: AgentLogEntry[];
  };
  videoId: string;
  videoDuration?: number;
  onSeek?: (ts: number) => void;
}

export function ModerationReportPanel({
  result,
  videoId,
  videoDuration,
  onSeek,
}: ModerationReportPanelProps) {
  const violations: AiViolation[] = result.violations ?? [];
  const agentLog: AgentLogEntry[] = (result as any).agent_log ?? [];
  const summary = result.ai_summary ?? result.report?.summary ?? '';

  return (
    <div className="space-y-5">
      {/* 1. Verdict */}
      <VerdictHeader
        status={result.status}
        confidence={result.overall_confidence ?? 0}
        processingTime="8.5s"
        policy="Enterprise Content Policy v2.3"
      />

      {/* 2. AI summary */}
      {summary && <AiSummaryCard summary={summary} />}

      {/* 3. Violation cards */}
      {violations.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-destructive" />
            Violations Detected ({violations.length})
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {violations.map((v, i) => (
              <ViolationDetailCard key={i} v={v} index={i} />
            ))}
          </div>
        </div>
      )}

      {/* 4. Timeline */}
      {violations.length > 0 && (
        <ViolationTimeline
          violations={violations}
          videoDuration={videoDuration}
          onSeek={onSeek}
        />
      )}

      {/* 5. Agent log */}
      {agentLog.length > 0 && (
        <AgentActivityLog entries={agentLog} animate={false} />
      )}

      {/* 6. Actions */}
      <ActionPanel videoId={videoId} />
    </div>
  );
}
