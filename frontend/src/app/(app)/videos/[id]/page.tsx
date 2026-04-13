'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { VideoPlayer } from '@/components/video/VideoPlayer';
import { FrameInspector } from '@/components/video/FrameInspector';
import { ModerationBadge } from '@/components/moderation/ModerationBadge';
import { ViolationCard } from '@/components/moderation/ViolationCard';
import { useVideo } from '@/hooks/useVideo';
import { useModerationResult } from '@/hooks/useModeration';
import { formatDistanceToNow } from 'date-fns';
import { VIDEO_STATUS_LABELS } from '@/lib/constants';

export default function VideoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [currentTime, setCurrentTime] = useState(0);

  const { data: video, isLoading: videoLoading } = useVideo(id);
  const { data: modResult, isLoading: modLoading } = useModerationResult(id);

  const violations = modResult?.report?.violations ?? [];

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

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.back()} aria-label="Go back">
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold truncate">{video.title}</h1>
          <Badge variant="secondary">{VIDEO_STATUS_LABELS[video.status]}</Badge>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Player */}
        <div className="space-y-4 lg:col-span-2">
          {video.playback_url ? (
            <VideoPlayer
              url={video.playback_url}
              violations={violations}
              onTimeUpdate={setCurrentTime}
            />
          ) : (
            <div className="flex aspect-video items-center justify-center rounded-lg border bg-muted text-muted-foreground">
              Video not yet available for playback
            </div>
          )}

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div>
              <p className="text-muted-foreground">Status</p>
              <p className="font-medium">{VIDEO_STATUS_LABELS[video.status]}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Source</p>
              <p className="font-medium capitalize">{video.source}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Uploaded</p>
              <p className="font-medium">
                {formatDistanceToNow(new Date(video.created_at), { addSuffix: true })}
              </p>
            </div>
            {video.s3_key && (
              <div>
                <p className="text-muted-foreground">Storage key</p>
                <p className="font-mono text-xs truncate">{video.s3_key}</p>
              </div>
            )}
          </div>
        </div>

        {/* Side panel */}
        <div className="space-y-4">
          {/* Moderation summary */}
          {modLoading ? (
            <Skeleton className="h-32 w-full" />
          ) : modResult ? (
            <div className="rounded-lg border bg-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Moderation</h3>
                <ModerationBadge status={modResult.status} />
              </div>
              {modResult.report?.recommended_action && (
                <p className="text-sm text-muted-foreground">
                  Recommended action:{' '}
                  <span className="font-medium capitalize">
                    {modResult.report.recommended_action}
                  </span>
                </p>
              )}
              {modResult.report?.summary && (
                <p className="text-sm">{modResult.report.summary}</p>
              )}
            </div>
          ) : null}

          {/* Frame inspector */}
          <FrameInspector
            currentTime={currentTime}
            violations={violations}
            isLoading={modLoading}
          />
        </div>
      </div>

      {/* Violations tab */}
      {violations.length > 0 && (
        <Tabs defaultValue="violations">
          <TabsList>
            <TabsTrigger value="violations">
              Violations ({violations.length})
            </TabsTrigger>
          </TabsList>
          <TabsContent value="violations" className="mt-4">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {violations.map((v) => (
                <ViolationCard key={v.id} violation={v} />
              ))}
            </div>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
