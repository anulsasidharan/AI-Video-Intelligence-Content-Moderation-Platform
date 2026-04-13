'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  AlertTriangle,
  ArrowLeft,
  Eye,
  Radio,
  ShieldCheck,
  ShieldOff,
  ShieldX,
  Zap,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { StreamCapture } from '@/components/live/StreamCapture';
import { LiveAlertFeed, type LiveEvent } from '@/components/live/LiveAlertFeed';
import { apiClient } from '@/lib/api';
import { API_V1, WS_URL } from '@/lib/constants';

// ── Types ──────────────────────────────────────────────────────────────────────

interface StreamDetail {
  id: string;
  title: string;
  status: string;
  moderation_active: boolean;
  moderation_started_at: string | null;
  moderation_stopped_at: string | null;
  frames_processed: number;
  ingest_url: string | null;
  created_at: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function buildWsUrl(streamId: string): string {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') ?? '' : '';
  // Convert http(s) base URL to ws(s)
  const base = WS_URL.replace(/^http/, 'ws');
  return `${base}${API_V1}/live/ws/streams/${streamId}?token=${encodeURIComponent(token)}`;
}

// ── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon,
  highlight,
}: {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <Card className={highlight ? 'border-red-400 dark:border-red-600' : ''}>
      <CardHeader className="flex flex-row items-center justify-between pb-1 pt-3 px-4">
        <CardTitle className="text-xs font-medium text-muted-foreground">{label}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent className="px-4 pb-3">
        <p className={`text-2xl font-bold ${highlight ? 'text-red-600 dark:text-red-400' : ''}`}>
          {value}
        </p>
      </CardContent>
    </Card>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function LiveStreamDetailPage() {
  const { streamId } = useParams<{ streamId: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  // ── Server state ───────────────────────────────────────────────────────────

  const { data: stream, isLoading } = useQuery<StreamDetail>({
    queryKey: ['live', 'stream', streamId],
    queryFn: () => apiClient.get<StreamDetail>(`/live/streams/${streamId}`),
    refetchInterval: 15_000,
  });

  const { mutate: startModeration, isPending: starting } = useMutation({
    mutationFn: () => apiClient.post<StreamDetail>(`/live/streams/${streamId}/start-moderation`),
    onSuccess: (updated) => {
      queryClient.setQueryData(['live', 'stream', streamId], updated);
      toast.success('Moderation started');
    },
    onError: () => toast.error('Failed to start moderation'),
  });

  const { mutate: stopModeration, isPending: stopping } = useMutation({
    mutationFn: () => apiClient.post<StreamDetail>(`/live/streams/${streamId}/stop-moderation`),
    onSuccess: (updated) => {
      queryClient.setQueryData(['live', 'stream', streamId], updated);
      toast.success('Moderation stopped');
    },
    onError: () => toast.error('Failed to stop moderation'),
  });

  // ── WebSocket + live events ────────────────────────────────────────────────

  const [events, setEvents] = useState<LiveEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  // Derived stats from events
  const violationCount = events.filter(
    (e) => e.event === 'frame.moderated' && !e.overall_safe,
  ).length;
  const minorAlertCount = events.filter(
    (e) => e.event === 'frame.moderated' && e.face_analysis?.has_minor,
  ).length;
  const framesAnalysed = events.filter((e) => e.event === 'frame.moderated').length;

  const connectWs = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current && wsRef.current.readyState < WebSocket.CLOSING) return;

    const ws = new WebSocket(buildWsUrl(streamId));
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      // Clear any pending reconnect
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current);
        reconnectRef.current = null;
      }
      // Start heartbeat
      heartbeatRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping');
      }, 30_000);
    };

    ws.onmessage = (msg) => {
      if (!mountedRef.current) return;
      try {
        const data = JSON.parse(msg.data as string);
        if (data === 'pong' || typeof data !== 'object') return;

        const evt: LiveEvent = {
          id: crypto.randomUUID(),
          timestamp: new Date(),
          ...data,
        };
        setEvents((prev) => [...prev.slice(-199), evt]); // keep last 200

        // Sync moderation_active from server events
        if (evt.event === 'moderation.started') {
          queryClient.setQueryData<StreamDetail>(['live', 'stream', streamId], (old) =>
            old ? { ...old, moderation_active: true } : old,
          );
        } else if (evt.event === 'moderation.stopped' || evt.event === 'stream.stopped') {
          queryClient.setQueryData<StreamDetail>(['live', 'stream', streamId], (old) =>
            old ? { ...old, moderation_active: false } : old,
          );
        }
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
        heartbeatRef.current = null;
      }
      if (mountedRef.current) {
        // Auto-reconnect after 4 seconds
        reconnectRef.current = setTimeout(connectWs, 4_000);
      }
    };

    ws.onerror = () => ws.close();
  }, [streamId, queryClient]);

  useEffect(() => {
    mountedRef.current = true;
    connectWs();
    return () => {
      mountedRef.current = false;
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      wsRef.current?.close();
    };
  }, [connectWs]);

  // ── Render ────────────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="space-y-6 pt-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      </div>
    );
  }

  if (!stream) {
    return (
      <div className="pt-6 text-center text-muted-foreground">
        Stream not found.{' '}
        <Button variant="link" onClick={() => router.back()}>
          Go back
        </Button>
      </div>
    );
  }

  const moderationActive = stream.moderation_active;

  return (
    <div className="space-y-6 pt-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.back()} aria-label="Go back">
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-bold truncate">{stream.title}</h1>
            <Badge variant={stream.status === 'active' ? 'default' : 'secondary'}>
              {stream.status.toUpperCase()}
            </Badge>
            {moderationActive && (
              <Badge variant="destructive" className="animate-pulse">
                <Radio className="mr-1 h-3 w-3" />
                LIVE MODERATION
              </Badge>
            )}
          </div>
          <p className="font-mono text-xs text-muted-foreground truncate">{stream.id}</p>
        </div>

        {/* Start / Stop moderation */}
        {moderationActive ? (
          <Button
            variant="destructive"
            onClick={() => stopModeration()}
            disabled={stopping}
            className="shrink-0"
          >
            <ShieldX className="mr-2 h-4 w-4" />
            {stopping ? 'Stopping…' : 'Stop Moderation'}
          </Button>
        ) : (
          <Button
            onClick={() => startModeration()}
            disabled={starting || stream.status !== 'active'}
            className="shrink-0"
          >
            <ShieldCheck className="mr-2 h-4 w-4" />
            {starting ? 'Starting…' : 'Start Moderation'}
          </Button>
        )}
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Frames Analysed"
          value={framesAnalysed}
          icon={<Eye className="h-4 w-4 text-muted-foreground" />}
        />
        <StatCard
          label="Violations Detected"
          value={violationCount}
          highlight={violationCount > 0}
          icon={<AlertTriangle className="h-4 w-4 text-muted-foreground" />}
        />
        <StatCard
          label="Minor Alerts"
          value={minorAlertCount}
          highlight={minorAlertCount > 0}
          icon={<ShieldOff className="h-4 w-4 text-muted-foreground" />}
        />
        <StatCard
          label="Total Events"
          value={events.length}
          icon={<Zap className="h-4 w-4 text-muted-foreground" />}
        />
      </div>

      {/* Main grid: camera capture left, alert feed right */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Camera capture — wider column */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Camera Capture</CardTitle>
            </CardHeader>
            <CardContent>
              <StreamCapture
                streamId={streamId}
                mode="camera"
                captureIntervalSeconds={3}
                moderationActive={moderationActive}
                onFrameSubmitted={(count) => {
                  // Optimistically update frames_processed in cache
                  queryClient.setQueryData<StreamDetail>(['live', 'stream', streamId], (old) =>
                    old ? { ...old, frames_processed: (old.frames_processed ?? 0) + count } : old,
                  );
                }}
              />
            </CardContent>
          </Card>

          {/* Stream info */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Stream Info</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-2 text-xs">
                <div>
                  <dt className="text-muted-foreground">Stream ID</dt>
                  <dd className="font-mono break-all">{stream.id}</dd>
                </div>
                {stream.ingest_url && (
                  <div>
                    <dt className="text-muted-foreground">Ingest URL</dt>
                    <dd className="font-mono break-all">{stream.ingest_url}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-muted-foreground">Frames Processed (server)</dt>
                  <dd>{stream.frames_processed}</dd>
                </div>
                {stream.moderation_started_at && (
                  <div>
                    <dt className="text-muted-foreground">Moderation started</dt>
                    <dd>{new Date(stream.moderation_started_at).toLocaleString()}</dd>
                  </div>
                )}
                {stream.moderation_stopped_at && (
                  <div>
                    <dt className="text-muted-foreground">Moderation stopped</dt>
                    <dd>{new Date(stream.moderation_stopped_at).toLocaleString()}</dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>
        </div>

        {/* Alert feed — wider column */}
        <div className="lg:col-span-3">
          <Card className="h-full">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold">Live Alert Feed</CardTitle>
                {events.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs h-7"
                    onClick={() => setEvents([])}
                  >
                    Clear
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <LiveAlertFeed events={events} maxHeight="560px" />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
