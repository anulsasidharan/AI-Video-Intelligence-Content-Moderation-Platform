'use client';

import { useRef, useState, useCallback } from 'react';
import ReactPlayer from 'react-player/lazy';
import { Pause, Play, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { TimelineAnnotation } from './TimelineAnnotation';
import { formatDuration } from '@/lib/utils';
import type { Violation } from '@/types/moderation';

interface VideoPlayerProps {
  url: string;
  violations?: Violation[];
  onTimeUpdate?: (seconds: number) => void;
}

export function VideoPlayer({ url, violations = [], onTimeUpdate }: VideoPlayerProps) {
  const playerRef = useRef<ReactPlayer>(null);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [volume, setVolume] = useState(0.8);
  const [played, setPlayed] = useState(0); // 0-1 fraction
  const [playedSeconds, setPlayedSeconds] = useState(0);
  const [duration, setDuration] = useState(0);
  const [seeking, setSeeking] = useState(false);

  const handleProgress = useCallback(
    ({ playedSeconds, played }: { playedSeconds: number; played: number }) => {
      if (!seeking) {
        setPlayedSeconds(playedSeconds);
        setPlayed(played);
        onTimeUpdate?.(playedSeconds);
      }
    },
    [seeking, onTimeUpdate]
  );

  const handleSeekToSeconds = (seconds: number) => {
    playerRef.current?.seekTo(seconds, 'seconds');
    setPlayedSeconds(seconds);
    setPlayed(seconds / duration);
  };

  const handleSliderSeek = (value: number[]) => {
    setSeeking(true);
    setPlayed(value[0]);
    setPlayedSeconds(value[0] * duration);
  };

  const handleSliderSeekEnd = (value: number[]) => {
    setSeeking(false);
    playerRef.current?.seekTo(value[0]);
  };

  return (
    <div className="overflow-hidden rounded-lg border bg-black">
      {/* Video */}
      <div className="relative aspect-video w-full">
        <ReactPlayer
          ref={playerRef}
          url={url}
          playing={playing}
          muted={muted}
          volume={volume}
          width="100%"
          height="100%"
          onProgress={handleProgress}
          onDuration={setDuration}
          onEnded={() => setPlaying(false)}
          style={{ position: 'absolute', top: 0, left: 0 }}
          config={{ file: { attributes: { controlsList: 'nodownload' } } }}
        />
      </div>

      {/* Controls */}
      <div className="space-y-2 bg-background/95 p-3">
        {/* Timeline with violation markers */}
        <TimelineAnnotation
          violations={violations}
          duration={duration}
          currentTime={playedSeconds}
          onSeek={handleSeekToSeconds}
        />

        {/* Scrubber */}
        <Slider
          value={[played]}
          min={0}
          max={1}
          step={0.001}
          onValueChange={handleSliderSeek}
          onValueCommit={handleSliderSeekEnd}
          className="w-full"
          aria-label="Video progress"
        />

        <div className="flex items-center justify-between">
          {/* Play/pause + time */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setPlaying((p) => !p)}
              aria-label={playing ? 'Pause' : 'Play'}
            >
              {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </Button>
            <span className="text-xs tabular-nums text-muted-foreground">
              {formatDuration(playedSeconds)} / {formatDuration(duration)}
            </span>
          </div>

          {/* Volume */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setMuted((m) => !m)}
              aria-label={muted ? 'Unmute' : 'Mute'}
            >
              {muted || volume === 0 ? (
                <VolumeX className="h-4 w-4" />
              ) : (
                <Volume2 className="h-4 w-4" />
              )}
            </Button>
            <Slider
              value={[muted ? 0 : volume]}
              min={0}
              max={1}
              step={0.05}
              onValueChange={([v]) => {
                setVolume(v);
                setMuted(v === 0);
              }}
              className="w-20"
              aria-label="Volume"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
