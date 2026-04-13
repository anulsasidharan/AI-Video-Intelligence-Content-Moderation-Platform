'use client';

import { useState } from 'react';
import { CheckCircle, XCircle, X, Bot, Shield, AlertTriangle, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { ModerationBadge } from './ModerationBadge';
import { useSubmitReview } from '@/hooks/useModeration';
import { formatDistanceToNow } from 'date-fns';
import type { AiViolation, ModerationQueueItem, ReviewAction } from '@/types/moderation';

interface ReviewPanelProps {
  item: ModerationQueueItem;
  onClose: () => void;
}

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'bg-red-100 border-red-300 text-red-800',
  high: 'bg-orange-100 border-orange-300 text-orange-800',
  medium: 'bg-yellow-100 border-yellow-300 text-yellow-800',
  low: 'bg-blue-100 border-blue-300 text-blue-800',
};

function ViolationItem({ v }: { v: AiViolation }) {
  return (
    <div className={`rounded-md border p-3 text-xs space-y-1 ${SEVERITY_COLOR[v.severity] ?? SEVERITY_COLOR.low}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold capitalize">{v.category.replace(/_/g, ' ')}</span>
        <div className="flex items-center gap-1.5 shrink-0">
          <Badge variant="outline" className="text-[10px] capitalize px-1.5 py-0">
            {v.severity}
          </Badge>
          <span className="tabular-nums">{Math.round(v.confidence * 100)}%</span>
        </div>
      </div>
      {v.description && (
        <p className="leading-snug opacity-90">{v.description}</p>
      )}
      {v.timestamp != null && (
        <p className="opacity-70">@ {v.timestamp.toFixed(1)}s</p>
      )}
    </div>
  );
}

export function ReviewPanel({ item, onClose }: ReviewPanelProps) {
  const [notes, setNotes] = useState('');
  const { mutate: submitReview, isPending } = useSubmitReview();

  const handleAction = (action: ReviewAction) => {
    const reviewId = item.moderation_result_id ?? item.id;
    submitReview(
      { id: reviewId, body: { action, notes: notes.trim() || undefined } },
      { onSuccess: onClose }
    );
  };

  const violations = item.violations ?? item.report?.violations ?? [];
  const confidencePct = item.overall_confidence != null
    ? Math.round(item.overall_confidence * 100)
    : null;

  // Parse ai_summary into sections (format: "Content...\n\nAI Reasoning: ...\n\nPolicy Triggers: ...")
  const summaryLines = (item.ai_summary ?? '').split('\n\n');
  const contentSummary = summaryLines[0] || null;
  const reasoningLine = summaryLines.find(l => l.startsWith('AI Reasoning:'));
  const policyLine = summaryLines.find(l => l.startsWith('Policy Triggers:'));
  const reasoning = reasoningLine ? reasoningLine.replace('AI Reasoning: ', '') : null;
  const policyTriggers = policyLine
    ? policyLine.replace('Policy Triggers: ', '').split(', ').filter(Boolean)
    : [];

  const isAlreadyDecided = item.status !== 'pending' && item.status !== 'in_review';

  return (
    <aside className="flex h-full w-[26rem] flex-col border-l bg-card" aria-label="AI decision detail">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-muted-foreground" />
          <h2 className="font-semibold text-sm">
            {item.video_title ?? (item.video_id ? `Video ${item.video_id.slice(0, 8)}…` : 'Decision Detail')}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <ModerationBadge status={item.status} />
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close panel">
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-4 p-4">

          {/* Confidence */}
          {confidencePct !== null && (
            <div className="flex items-center gap-3 rounded-md bg-muted/50 px-3 py-2">
              <Shield className="h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="flex-1">
                <p className="text-xs font-medium text-muted-foreground">AI Confidence</p>
                <div className="mt-1 h-1.5 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      confidencePct >= 80 ? 'bg-primary' : confidencePct >= 50 ? 'bg-yellow-500' : 'bg-red-400'
                    }`}
                    style={{ width: `${confidencePct}%` }}
                  />
                </div>
              </div>
              <span className="text-sm font-semibold tabular-nums">{confidencePct}%</span>
            </div>
          )}

          {/* Content summary */}
          {contentSummary && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <Info className="h-3.5 w-3.5 text-muted-foreground" />
                <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Content Summary
                </h3>
              </div>
              <p className="text-sm leading-relaxed">{contentSummary}</p>
            </div>
          )}

          {/* AI Reasoning */}
          {reasoning && (
            <>
              <Separator />
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5">
                  <Bot className="h-3.5 w-3.5 text-muted-foreground" />
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Decision Reasoning
                  </h3>
                </div>
                <p className="text-sm leading-relaxed text-foreground/90">{reasoning}</p>
              </div>
            </>
          )}

          {/* Policy triggers */}
          {policyTriggers.length > 0 && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Policy Triggers
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {policyTriggers.map((t) => (
                  <Badge key={t} variant="secondary" className="text-xs">
                    {t}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Violations */}
          {violations.length > 0 && (
            <>
              <Separator />
              <div className="space-y-2">
                <div className="flex items-center gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5 text-muted-foreground" />
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Violations Detected ({violations.length})
                  </h3>
                </div>
                <div className="space-y-2">
                  {(violations as AiViolation[]).map((v, i) => (
                    <ViolationItem key={i} v={v} />
                  ))}
                </div>
              </div>
            </>
          )}

          {violations.length === 0 && !contentSummary && !reasoning && (
            <p className="text-sm text-muted-foreground italic">
              AI analysis not yet available for this item.
            </p>
          )}

          <Separator />

          {/* Meta */}
          <div className="space-y-1 text-xs text-muted-foreground">
            {item.ai_model && <p>Model: <span className="font-mono">{item.ai_model}</span></p>}
            <p>Created: {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}</p>
            {item.moderation_result_id && (
              <p>Result ID: <span className="font-mono">{item.moderation_result_id.slice(0, 8)}…</span></p>
            )}
          </div>

          {/* Override notes (only if already decided) */}
          {!isAlreadyDecided && (
            <div className="space-y-2">
              <Label htmlFor="review-notes" className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Override Notes (optional)
              </Label>
              <Textarea
                id="review-notes"
                placeholder="Reason for overriding the AI decision…"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                maxLength={1000}
              />
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Override actions — only shown when a human wants to correct the AI */}
      {!isAlreadyDecided && (
        <div className="border-t p-4 space-y-2">
          <p className="text-xs text-muted-foreground text-center">Override AI decision</p>
          <Button
            className="w-full gap-2 bg-green-600 hover:bg-green-700 text-white"
            onClick={() => handleAction('approve')}
            disabled={isPending}
          >
            <CheckCircle className="h-4 w-4" />
            Override → Approve
          </Button>
          <Button
            variant="destructive"
            className="w-full gap-2"
            onClick={() => handleAction('reject')}
            disabled={isPending}
          >
            <XCircle className="h-4 w-4" />
            Override → Reject
          </Button>
        </div>
      )}
    </aside>
  );
}
