'use client';

import Link from 'next/link';
import { Plus, Radio, StopCircle, ArrowRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { formatDistanceToNow } from 'date-fns';
import { ROUTES } from '@/lib/constants';

export interface StreamSummary {
  id: string;
  title?: string;
  status: 'active' | 'paused' | 'stopped' | 'error';
  created_at: string;
  alert_count?: number;
}

interface StreamMonitorProps {
  streams: StreamSummary[];
  onStop?: (id: string) => void;
  isLoading?: boolean;
  onAddStream?: () => void;
}

const statusVariant: Record<StreamSummary['status'], 'destructive' | 'secondary' | 'warning' | 'success'> = {
  active: 'destructive',
  paused: 'warning',
  stopped: 'secondary',
  error: 'destructive',
};

export function StreamMonitor({ streams, onStop, isLoading, onAddStream }: StreamMonitorProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    );
  }

  if (streams.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center">
        <Radio className="mb-3 h-8 w-8 text-muted-foreground" />
        <p className="font-medium">No active streams</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Add a stream source to start AI-powered live monitoring.
        </p>
        {onAddStream && (
          <Button className="mt-4" onClick={onAddStream}>
            <Plus className="mr-2 h-4 w-4" />
            New Stream
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {streams.map((stream) => (
        <Card key={stream.id}>
          <CardContent className="flex items-center justify-between gap-3 p-4">
            <div className="flex items-center gap-3 min-w-0">
              <Radio
                className={`h-4 w-4 shrink-0 ${
                  stream.status === 'active' ? 'text-red-500 animate-pulse' : 'text-muted-foreground'
                }`}
              />
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">
                  {stream.title ?? stream.id.slice(0, 12)}…
                </p>
                <p className="text-xs text-muted-foreground">
                  Started {formatDistanceToNow(new Date(stream.created_at), { addSuffix: true })}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Badge variant={statusVariant[stream.status]}>
                {stream.status.toUpperCase()}
              </Badge>
              {(stream.alert_count ?? 0) > 0 && (
                <Badge variant="warning" className="text-xs">
                  {stream.alert_count} alert{stream.alert_count !== 1 ? 's' : ''}
                </Badge>
              )}
              {onStop && stream.status === 'active' && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => onStop(stream.id)}
                  aria-label="Stop stream"
                >
                  <StopCircle className="h-4 w-4 text-destructive" />
                </Button>
              )}
              <Button variant="ghost" size="icon" className="h-8 w-8" asChild>
                <Link href={ROUTES.liveStream(stream.id)} aria-label="View stream">
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
