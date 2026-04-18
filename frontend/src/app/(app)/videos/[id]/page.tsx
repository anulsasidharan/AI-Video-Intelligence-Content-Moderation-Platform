'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { VideoPlayer } from '@/components/video/VideoPlayer';
import { ProcessingPipelineCard } from '@/components/video/ProcessingPipelineCard';
import { AgentActivityLog } from '@/components/video/AgentActivityLog';
import { ModerationReportPanel } from '@/components/moderation/ModerationReportPanel';
import { useVideo } from '@/hooks/useVideo';
import { useModerationResult } from '@/hooks/useModeration';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { VIDEO_STATUS_LABELS } from '@/lib/constants';
import type { AgentLogEntry } from '@/components/video/AgentActivityLog';

export default function VideoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [currentTime, setCurrentTime] = useState(0);

  const { data: video, isLoading: videoLoading } = useVideo(id);
  const { data: modResult, isLoading: modLoading } = useModerationResult(id);

  // Fetch agent log separately
  const { data: agentLogData } = useQuery<AgentLogEntry[]>({
    queryKey: ['videos', id, 'agent-log'],
    queryFn: () => apiClient.get<AgentLogEntry[]>(`/videos/${id}/agent-log`),
    enabled: !!id,
  });

  const violations = modResult?.report?.violations ?? [];
  const isProcessing = video?.status === 'processing';

  if (videoLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="aspect-video w-full rounded-lg" />
        <Skeleton className="h-32 w-full rounded-lg" />
      </div>
    );
  }

  if (!video) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center">
        <p className="text-muted-foreground">Video not found.</p>
        <Button variant="outline" className="mt-4" onClick={() => router.back()}>
          Go back
        </Button>
      </div>
    );
  }

  // Merge agent_log from modResult into the result object
  const enrichedResult = modResult
    ? { ...modResult, agent_log: agentLogData ?? (modResult as any).agent_log ?? [] }
    : null;

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.back()} aria-label="Go back">
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex items-center gap-3 min-w-0">
          <h1 className="text-2xl font-bold truncate">{video.title}</h1>
          <Badge variant="secondary" className="flex-shrink-0">
            {VIDEO_STATUS_LABELS[video.status]}
          </Badge>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-5">
        {/* Left: player + metadata (wider) */}
        <div className="space-y-4 xl:col-span-3">
          {video.playback_url ? (
            <VideoPlayer
              url={video.playback_url}
              violations={violations}
              onTimeUpdate={setCurrentTime}
            />
          ) : (
            <div className="flex aspect-video items-center justify-center rounded-lg border bg-muted text-muted-foreground text-sm">
              Video not yet available for playback
            </div>
          )}

          {/* Metadata strip */}
          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div>
              <p className="text-muted-foreground text-xs">Status</p>
              <p className="font-medium">{VIDEO_STATUS_LABELS[video.status]}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Source</p>
              <p className="font-medium capitalize">{video.source}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Uploaded</p>
              <p className="font-medium">
                {formatDistanceToNow(new Date(video.created_at), { addSuffix: true })}
              </p>
            </div>
            {video.s3_key && (
              <div>
                <p className="text-muted-foreground text-xs">Storage key</p>
                <p className="font-mono text-xs truncate">{video.s3_key}</p>
              </div>
            )}
          </div>

          {/* Processing pipeline — shown when video is still processing */}
          {isProcessing && (
            <ProcessingPipelineCard autoStart />
          )}
        </div>

        {/* Right: moderation panel */}
        <div className="xl:col-span-2 space-y-4">
          {isProcessing ? (
            /* Live agent log while processing */
            agentLogData ? (
              <AgentActivityLog
                entries={agentLogData}
                animate
                lineDelay={400}
              />
            ) : (
              <Skeleton className="h-64 w-full rounded-lg" />
            )
          ) : modLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-24 w-full rounded-xl" />
              <Skeleton className="h-32 w-full rounded-xl" />
              <Skeleton className="h-32 w-full rounded-xl" />
            </div>
          ) : enrichedResult ? (
            <Tabs defaultValue="report">
              <TabsList className="w-full">
                <TabsTrigger value="report" className="flex-1">Moderation Report</TabsTrigger>
                <TabsTrigger value="log" className="flex-1">Agent Log</TabsTrigger>
              </TabsList>

              <TabsContent value="report" className="mt-4">
                <ModerationReportPanel
                  result={enrichedResult}
                  videoId={id}
                  videoDuration={video.duration ?? 754}
                  onSeek={setCurrentTime}
                />
              </TabsContent>

              <TabsContent value="log" className="mt-4">
                <AgentActivityLog
                  entries={enrichedResult.agent_log as AgentLogEntry[]}
                  animate={false}
                />
              </TabsContent>
            </Tabs>
          ) : (
            <div className="rounded-xl border bg-muted/30 p-6 text-center text-sm text-muted-foreground">
              No moderation result yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
