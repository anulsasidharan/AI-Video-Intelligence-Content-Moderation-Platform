'use client';

import { useEffect, useRef, useState } from 'react';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PipelineStage {
  key: string;
  label: string;
  description: string;
  duration: number; // simulated ms to complete this stage
}

const STAGES: PipelineStage[] = [
  { key: 'upload', label: 'Uploading to GCS', description: 'Streaming file to Google Cloud Storage via presigned URL', duration: 1800 },
  { key: 'frames', label: 'Extracting frames', description: 'FFmpeg sampling 84 keyframes @ 7 fps for visual analysis', duration: 1400 },
  { key: 'audio', label: 'Transcribing audio', description: 'Whisper-large-v3 generating timestamped transcript with speaker diarization', duration: 2000 },
  { key: 'agents', label: 'Dispatching AI agents', description: 'LangGraph OrchestratorAgent spawning ContentAnalyzer, SafetyChecker, MetadataExtractor, SceneClassifier, OCRTool', duration: 1200 },
  { key: 'report', label: 'Generating report', description: 'ReportGenerator synthesising violations, confidence scores, and policy decisions', duration: 1000 },
];

type StageStatus = 'pending' | 'active' | 'done';

interface ProcessingPipelineCardProps {
  /** Start processing immediately on mount */
  autoStart?: boolean;
  /** Called when all stages complete */
  onComplete?: () => void;
  className?: string;
}

export function ProcessingPipelineCard({
  autoStart = true,
  onComplete,
  className,
}: ProcessingPipelineCardProps) {
  const [stageIndex, setStageIndex] = useState<number>(autoStart ? 0 : -1);
  const [stageProgress, setStageProgress] = useState(0);
  const [done, setDone] = useState(false);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    if (stageIndex < 0 || done) return;
    if (stageIndex >= STAGES.length) {
      setDone(true);
      onCompleteRef.current?.();
      return;
    }

    const stage = STAGES[stageIndex];
    const tickMs = 60;
    const ticks = Math.ceil(stage.duration / tickMs);
    let tick = 0;
    setStageProgress(0);

    const interval = setInterval(() => {
      tick++;
      setStageProgress(Math.min((tick / ticks) * 100, 100));
      if (tick >= ticks) {
        clearInterval(interval);
        setStageIndex((i) => i + 1);
      }
    }, tickMs);

    return () => clearInterval(interval);
  }, [stageIndex, done]);

  const totalPct = done
    ? 100
    : Math.round(((stageIndex + stageProgress / 100) / STAGES.length) * 100);

  const getStatus = (i: number): StageStatus => {
    if (done || i < stageIndex) return 'done';
    if (i === stageIndex) return 'active';
    return 'pending';
  };

  return (
    <div className={cn('rounded-xl border bg-card p-6 space-y-5', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-sm">AI Processing Pipeline</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            LangGraph · GPT-4o · Whisper · FFmpeg
          </p>
        </div>
        <span className="text-sm font-bold tabular-nums text-primary">{totalPct}%</span>
      </div>

      {/* Overall progress bar */}
      <div className="space-y-1.5">
        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all duration-300 ease-out"
            style={{ width: `${totalPct}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground">
          {done ? 'Analysis complete' : `Step ${Math.min(stageIndex + 1, STAGES.length)} of ${STAGES.length}`}
        </p>
      </div>

      {/* Stage list */}
      <ol className="space-y-4">
        {STAGES.map((stage, i) => {
          const status = getStatus(i);
          return (
            <li key={stage.key} className="flex gap-3">
              {/* Icon */}
              <div className="flex-shrink-0 mt-0.5">
                {status === 'done' ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : status === 'active' ? (
                  <Loader2 className="h-5 w-5 text-primary animate-spin" />
                ) : (
                  <Circle className="h-5 w-5 text-muted-foreground/40" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <p
                    className={cn(
                      'text-sm font-medium',
                      status === 'pending' && 'text-muted-foreground',
                      status === 'active' && 'text-foreground',
                      status === 'done' && 'text-green-600 dark:text-green-400',
                    )}
                  >
                    {stage.label}
                    {status === 'done' && <span className="ml-1.5 font-normal text-xs">✓</span>}
                  </p>
                  {status === 'active' && (
                    <span className="text-xs text-primary font-mono tabular-nums flex-shrink-0">
                      {Math.round(stageProgress)}%
                    </span>
                  )}
                </div>

                {/* Description — show for active and done stages */}
                {status !== 'pending' && (
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {stage.description}
                  </p>
                )}

                {/* Per-stage progress bar — only for active */}
                {status === 'active' && (
                  <div className="h-1 w-full rounded-full bg-muted overflow-hidden mt-1.5">
                    <div
                      className="h-full rounded-full bg-primary/70 transition-all duration-75 ease-linear"
                      style={{ width: `${stageProgress}%` }}
                    />
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ol>

      {done && (
        <div className="flex items-center gap-2 rounded-md bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 px-4 py-3 text-sm text-green-700 dark:text-green-400">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          Analysis complete — moderation report ready
        </div>
      )}
    </div>
  );
}
