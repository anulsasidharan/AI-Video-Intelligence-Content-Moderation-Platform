'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { Radio } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useStreamEvents } from '@/hooks/useWebSocket';
import { useModerationStore } from '@/stores/moderationStore';
import { formatDistanceToNow } from 'date-fns';

interface LiveFeedProps {
  streamId: string;
  className?: string;
}

export function LiveFeed({ streamId, className }: LiveFeedProps) {
  const [latestFrame, setLatestFrame] = useState<{
    url: string;
    timestamp: string;
    sequence: number;
  } | null>(null);
  const [streamStatus, setStreamStatus] = useState<string>('unknown');
  const { addLiveAlert } = useModerationStore();

  useStreamEvents(streamId, {
    onStatus: ({ status, timestamp }) => {
      setStreamStatus(status);
    },
    onFrame: ({ frame_url, timestamp, sequence }) => {
      setLatestFrame({ url: frame_url, timestamp, sequence });
    },
    onAlert: ({ category, confidence, timestamp }) => {
      addLiveAlert({
        id: `${streamId}-${timestamp}`,
        stream_id: streamId,
        category,
        confidence,
        timestamp,
      });
    },
  });

  const isLive = streamStatus === 'active';

  return (
    <div className={`overflow-hidden rounded-lg border bg-black ${className ?? ''}`}>
      {/* Status bar */}
      <div className="flex items-center justify-between bg-background/80 px-3 py-1.5">
        <div className="flex items-center gap-2">
          <Radio className={`h-3 w-3 ${isLive ? 'text-red-500 animate-pulse' : 'text-muted-foreground'}`} />
          <Badge variant={isLive ? 'destructive' : 'secondary'} className="text-xs">
            {isLive ? 'LIVE' : streamStatus.toUpperCase()}
          </Badge>
        </div>
        {latestFrame && (
          <span className="text-xs text-muted-foreground">
            Frame #{latestFrame.sequence} ·{' '}
            {formatDistanceToNow(new Date(latestFrame.timestamp), { addSuffix: true })}
          </span>
        )}
      </div>

      {/* Frame */}
      <div className="relative aspect-video w-full bg-black">
        {latestFrame ? (
          <Image
            src={latestFrame.url}
            alt="Live stream frame"
            fill
            className="object-contain"
            unoptimized
          />
        ) : (
          <div className="flex h-full items-center justify-center text-muted-foreground text-sm">
            {isLive ? 'Waiting for frames…' : 'Stream inactive'}
          </div>
        )}
      </div>
    </div>
  );
}
