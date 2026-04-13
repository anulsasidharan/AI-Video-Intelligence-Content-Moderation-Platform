'use client';

/**
 * StreamCapture
 *
 * Captures video frames from:
 *   - Webcam (getUserMedia) — for direct camera streams
 *   - A <video> element with a HLS/dash URL — for network streams
 *
 * At the configured interval it:
 *   1. Draws the current video frame onto a hidden canvas
 *   2. Exports as a base64 JPEG
 *   3. POSTs to POST /live/streams/{id}/frames
 *
 * Start/Stop button controls the capture loop. When stopped, no frames
 * are sent and no API calls are made — preventing runaway resource use.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { Camera, CameraOff, Video, VideoOff, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/api';

interface StreamCaptureProps {
  streamId: string;
  /** 'camera' = getUserMedia; 'url' = play a given stream URL */
  mode?: 'camera' | 'url';
  /** Only used when mode='url' */
  streamUrl?: string;
  /** Seconds between frame submissions (default 3) */
  captureIntervalSeconds?: number;
  /** Called each time a frame batch is submitted successfully */
  onFrameSubmitted?: (frameCount: number) => void;
  /** Whether moderation is active on the backend */
  moderationActive: boolean;
}

const JPEG_QUALITY = 0.7;
const FRAMES_PER_BATCH = 2; // frames to capture per interval tick

export function StreamCapture({
  streamId,
  mode = 'camera',
  streamUrl,
  captureIntervalSeconds = 3,
  onFrameSubmitted,
  moderationActive,
}: StreamCaptureProps) {
  const videoRef     = useRef<HTMLVideoElement>(null);
  const canvasRef    = useRef<HTMLCanvasElement>(null);
  const intervalRef  = useRef<ReturnType<typeof setInterval> | null>(null);
  const streamRef    = useRef<MediaStream | null>(null);

  const [capturing, setCapturing] = useState(false);
  const [frameCount, setFrameCount] = useState(0);
  const [error, setError]     = useState<string | null>(null);
  const [cameraReady, setCameraReady] = useState(false);

  // ── Camera initialisation ──────────────────────────────────────────────────

  const startCamera = useCallback(async () => {
    setError(null);
    try {
      if (mode === 'camera') {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, frameRate: 15 },
          audio: false,
        });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setCameraReady(true);
        }
      } else if (mode === 'url' && streamUrl && videoRef.current) {
        videoRef.current.src = streamUrl;
        await videoRef.current.play();
        setCameraReady(true);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Camera access failed';
      setError(msg);
      toast.error(`Camera error: ${msg}`);
    }
  }, [mode, streamUrl]);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
      videoRef.current.src = '';
    }
    setCameraReady(false);
  }, []);

  // Initialise camera on mount
  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, [startCamera, stopCamera]);

  // ── Frame capture loop ─────────────────────────────────────────────────────

  const captureFrame = useCallback((): string | null => {
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return null;

    canvas.width  = video.videoWidth  || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    // Return base64 data URL without the "data:image/jpeg;base64," prefix
    const dataUrl = canvas.toDataURL('image/jpeg', JPEG_QUALITY);
    return dataUrl.split(',')[1] ?? null;
  }, []);

  const submitFrames = useCallback(async () => {
    if (!moderationActive) return;

    const frames: string[] = [];
    for (let i = 0; i < FRAMES_PER_BATCH; i++) {
      const f = captureFrame();
      if (f) frames.push(f);
      // Small gap between frames in the same batch
      if (i < FRAMES_PER_BATCH - 1) await new Promise((r) => setTimeout(r, 200));
    }
    if (frames.length === 0) return;

    try {
      await apiClient.post(`/live/streams/${streamId}/frames`, {
        frames,
        transcript_hint: '',
      });
      setFrameCount((c) => c + frames.length);
      onFrameSubmitted?.(frames.length);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 429) {
        // Slow down — backend rate limited
        toast.warning('Frame rate too high — slowing capture');
      } else if (status === 409) {
        // Moderation was stopped on backend — sync UI
        stopCapture();
      }
    }
  }, [moderationActive, captureFrame, streamId, onFrameSubmitted]);

  const startCapture = useCallback(() => {
    if (intervalRef.current) return;
    setCapturing(true);
    intervalRef.current = setInterval(submitFrames, captureIntervalSeconds * 1000);
  }, [submitFrames, captureIntervalSeconds]);

  const stopCapture = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setCapturing(false);
  }, []);

  // Stop capture when moderation is deactivated externally
  useEffect(() => {
    if (!moderationActive && capturing) stopCapture();
  }, [moderationActive, capturing, stopCapture]);

  // Cleanup on unmount
  useEffect(() => () => stopCapture(), [stopCapture]);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-3">
      {/* Video preview */}
      <div className="relative overflow-hidden rounded-lg bg-black aspect-video">
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          autoPlay
          muted
          playsInline
        />
        <canvas ref={canvasRef} className="hidden" />

        {/* Status overlay */}
        <div className="absolute top-2 left-2 flex gap-2">
          {capturing && (
            <Badge variant="destructive" className="animate-pulse text-xs">
              ● CAPTURING
            </Badge>
          )}
          {moderationActive && !capturing && (
            <Badge variant="secondary" className="text-xs">
              MODERATION ON — NOT CAPTURING
            </Badge>
          )}
        </div>

        {/* Frame counter */}
        {frameCount > 0 && (
          <div className="absolute bottom-2 right-2 text-xs text-white/70 bg-black/40 rounded px-2 py-1">
            {frameCount} frames sent
          </div>
        )}

        {/* Camera not ready */}
        {!cameraReady && !error && (
          <div className="absolute inset-0 flex items-center justify-center text-white/60">
            <Camera className="h-8 w-8 animate-pulse" />
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/70 text-white gap-2 p-4 text-center">
            <AlertTriangle className="h-6 w-6 text-yellow-400" />
            <p className="text-sm">{error}</p>
            <Button size="sm" variant="outline" onClick={startCamera}>
              Retry
            </Button>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3">
        {capturing ? (
          <Button
            variant="destructive"
            onClick={stopCapture}
            className="flex-1"
          >
            <VideoOff className="mr-2 h-4 w-4" />
            Stop Capture
          </Button>
        ) : (
          <Button
            onClick={startCapture}
            disabled={!moderationActive || !cameraReady}
            className="flex-1"
          >
            <Video className="mr-2 h-4 w-4" />
            Start Capture
          </Button>
        )}

        {!moderationActive && (
          <p className="text-xs text-muted-foreground">
            Enable moderation first to start capturing
          </p>
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        Captures {FRAMES_PER_BATCH} frame{FRAMES_PER_BATCH > 1 ? 's' : ''} every {captureIntervalSeconds}s.
        Stop capture to conserve resources.
      </p>
    </div>
  );
}
