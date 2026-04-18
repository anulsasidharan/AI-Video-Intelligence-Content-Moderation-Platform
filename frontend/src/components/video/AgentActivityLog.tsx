'use client';

import { useEffect, useRef, useState } from 'react';
import { Terminal } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface AgentLogEntry {
  ts: string;
  agent: string;
  message: string;
  level: 'info' | 'warn' | 'error' | 'success';
}

interface AgentActivityLogProps {
  entries: AgentLogEntry[];
  /** When true, reveal entries one-by-one with a typewriter effect */
  animate?: boolean;
  /** ms between each new line appearing (only when animate=true) */
  lineDelay?: number;
  className?: string;
}

const levelStyles: Record<AgentLogEntry['level'], string> = {
  info: 'text-slate-300',
  warn: 'text-yellow-400',
  error: 'text-red-400',
  success: 'text-green-400',
};

const agentColors: Record<string, string> = {
  OrchestratorAgent: 'text-blue-400',
  ContentAnalyzer: 'text-indigo-400',
  AudioTranscriber: 'text-purple-400',
  SafetyChecker: 'text-orange-400',
  MetadataExtractor: 'text-cyan-400',
  SceneClassifier: 'text-teal-400',
  OCRTool: 'text-pink-400',
  ReportGenerator: 'text-yellow-400',
};

export function AgentActivityLog({
  entries,
  animate = false,
  lineDelay = 340,
  className,
}: AgentActivityLogProps) {
  const [visible, setVisible] = useState(animate ? 0 : entries.length);
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!animate) {
      setVisible(entries.length);
      return;
    }
    setVisible(0);
    const timers: ReturnType<typeof setTimeout>[] = [];
    entries.forEach((_, i) => {
      timers.push(setTimeout(() => setVisible(i + 1), i * lineDelay));
    });
    return () => timers.forEach(clearTimeout);
  }, [animate, entries, lineDelay]);

  // Auto-scroll to bottom as lines appear
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [visible]);

  const shownEntries = entries.slice(0, visible);
  const isStreaming = animate && visible < entries.length;

  return (
    <div className={cn('rounded-xl border bg-card overflow-hidden', className)}>
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b bg-muted/40">
        <Terminal className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">AI Agent Activity</span>
        <span className="ml-auto text-xs text-muted-foreground font-mono">LangGraph pipeline</span>
        {isStreaming && (
          <span className="flex items-center gap-1.5 text-xs text-primary">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            Live
          </span>
        )}
      </div>

      {/* Log area */}
      <div
        ref={containerRef}
        className="overflow-y-auto max-h-80 bg-slate-950 p-4 font-mono text-xs leading-relaxed"
      >
        {shownEntries.map((entry, i) => (
          <div key={i} className="flex gap-2 mb-1.5 group">
            <span className="text-slate-600 select-none flex-shrink-0 w-[72px]">[{entry.ts}]</span>
            <span className={cn('flex-shrink-0 w-[140px] font-semibold truncate', agentColors[entry.agent] ?? 'text-slate-400')}>
              {entry.agent}
            </span>
            <span className={cn('flex-1', levelStyles[entry.level])}>
              {entry.message}
            </span>
          </div>
        ))}

        {/* Blinking cursor while streaming */}
        {isStreaming && (
          <span className="text-muted-foreground animate-pulse">█</span>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Footer stats */}
      <div className="flex items-center gap-4 px-4 py-2.5 border-t bg-muted/20 text-xs text-muted-foreground">
        <span>{entries.filter((e) => e.level === 'error').length} violations flagged</span>
        <span>·</span>
        <span>{entries.filter((e) => e.level === 'warn').length} warnings</span>
        <span>·</span>
        <span>{entries.length} total events</span>
        {!isStreaming && visible === entries.length && (
          <>
            <span>·</span>
            <span className="text-green-500 font-medium">Pipeline complete</span>
          </>
        )}
      </div>
    </div>
  );
}
