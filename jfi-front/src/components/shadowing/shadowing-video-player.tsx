'use client';

import React, { useRef, useState, useEffect } from 'react';
import { ShadowingSegment } from '@/types';
import { Button } from '@/components/ui/button';
import {
  Play,
  Pause,
  RotateCcw,
  SkipBack,
  SkipForward,
  Repeat,
  Volume2,
  VolumeX,
} from 'lucide-react';

interface ShadowingVideoPlayerProps {
  videoUrl?: string | null;
  segments: ShadowingSegment[];
  currentSegment?: ShadowingSegment | null;
  onSelectSegment: (segment: ShadowingSegment) => void;
  onTimeUpdate?: (currentTime: number) => void;
}

function formatTime(seconds: number): string {
  if (isNaN(seconds) || seconds < 0) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

export function ShadowingVideoPlayer({
  videoUrl,
  segments,
  currentSegment,
  onSelectSegment,
  onTimeUpdate,
}: ShadowingVideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);
  const [isLooping, setIsLooping] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);

  // Play / Pause toggle
  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  // Seek time
  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!videoRef.current) return;
    const newTime = parseFloat(e.target.value);
    videoRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  // Replay current segment
  const replayCurrentSegment = () => {
    if (!videoRef.current || !currentSegment) return;
    videoRef.current.currentTime = currentSegment.start_time;
    videoRef.current.play();
    setIsPlaying(true);
  };

  // Jump to Previous segment
  const handlePrevSegment = () => {
    if (!segments || segments.length === 0) return;
    const currentIndex = currentSegment
      ? segments.findIndex((s) => s.id === currentSegment.id)
      : -1;
    const prevIndex = currentIndex > 0 ? currentIndex - 1 : 0;
    const target = segments[prevIndex];
    onSelectSegment(target);
    if (videoRef.current) {
      videoRef.current.currentTime = target.start_time;
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  // Jump to Next segment
  const handleNextSegment = () => {
    if (!segments || segments.length === 0) return;
    const currentIndex = currentSegment
      ? segments.findIndex((s) => s.id === currentSegment.id)
      : -1;
    const nextIndex =
      currentIndex !== -1 && currentIndex < segments.length - 1
        ? currentIndex + 1
        : segments.length - 1;
    const target = segments[nextIndex];
    onSelectSegment(target);
    if (videoRef.current) {
      videoRef.current.currentTime = target.start_time;
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  // Speed change
  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
    }
  };

  // Synchronize timeupdate
  const handleVideoTimeUpdate = () => {
    if (!videoRef.current) return;
    const curr = videoRef.current.currentTime;
    setCurrentTime(curr);
    if (onTimeUpdate) onTimeUpdate(curr);

    // Loop logic: if looping enabled and current segment exists
    if (isLooping && currentSegment) {
      if (curr >= currentSegment.end_time) {
        videoRef.current.currentTime = currentSegment.start_time;
        videoRef.current.play();
      }
    }
  };

  // Seek to segment when currentSegment changes externally (e.g. clicked in list)
  useEffect(() => {
    if (currentSegment && videoRef.current) {
      const diff = Math.abs(videoRef.current.currentTime - currentSegment.start_time);
      if (diff > 1.0) {
        videoRef.current.currentTime = currentSegment.start_time;
      }
    }
  }, [currentSegment]);

  return (
    <div className="space-y-4">
      {/* Video Display Container */}
      <div className="relative w-full aspect-video bg-black rounded-2xl overflow-hidden shadow-sm flex items-center justify-center">
        {videoUrl ? (
          <video
            ref={videoRef}
            src={videoUrl}
            onTimeUpdate={handleVideoTimeUpdate}
            onLoadedMetadata={() => {
              if (videoRef.current) {
                setDuration(videoRef.current.duration || 0);
              }
            }}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onClick={togglePlay}
            playsInline
            className="w-full h-full object-contain cursor-pointer"
          />
        ) : (
          <div className="text-stone-400 text-sm text-center p-6">
            Đang tải dữ liệu video hoặc video chưa sẵn sàng...
          </div>
        )}
      </div>

      {/* Control Bar */}
      <div className="p-4 rounded-2xl bg-white border border-stone-200/90 shadow-2xs space-y-3">
        {/* Seek Bar & Timers */}
        <div className="space-y-1">
          <input
            type="range"
            min={0}
            max={duration || 100}
            step={0.1}
            value={currentTime}
            onChange={handleSeek}
            aria-label="Thanh thời gian video"
            className="w-full h-1.5 bg-stone-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
          <div className="flex items-center justify-between text-xs text-stone-500 font-mono">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Buttons Row */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          {/* Main Controls: Prev, Replay, Play/Pause, Next */}
          <div className="flex items-center gap-1.5">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handlePrevSegment}
              title="Câu trước"
              className="h-9 w-9 p-0 border-stone-200"
            >
              <SkipBack className="w-4 h-4" />
            </Button>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={replayCurrentSegment}
              title="Nghe lại câu này"
              className="h-9 w-9 p-0 border-stone-200"
            >
              <RotateCcw className="w-4 h-4" />
            </Button>

            <Button
              type="button"
              size="sm"
              onClick={togglePlay}
              title={isPlaying ? 'Tạm dừng' : 'Phát'}
              className="h-9 px-4 font-semibold gap-1.5 shadow-xs"
            >
              {isPlaying ? (
                <>
                  <Pause className="w-4 h-4" />
                  <span className="text-xs">Tạm dừng</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span className="text-xs">Phát</span>
                </>
              )}
            </Button>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleNextSegment}
              title="Câu tiếp theo"
              className="h-9 w-9 p-0 border-stone-200"
            >
              <SkipForward className="w-4 h-4" />
            </Button>
          </div>

          {/* Secondary Controls: Loop toggle, Speed, Mute */}
          <div className="flex items-center gap-2">
            {/* Loop Toggle */}
            <Button
              type="button"
              variant={isLooping ? 'default' : 'outline'}
              size="sm"
              onClick={() => setIsLooping(!isLooping)}
              title="Lặp lại câu này"
              className={`h-9 px-2.5 text-xs gap-1 border-stone-200 ${
                isLooping ? 'bg-indigo-600 text-white' : 'text-stone-600'
              }`}
            >
              <Repeat className="w-3.5 h-3.5" />
              <span>Lặp lại câu</span>
            </Button>

            {/* Playback Speed */}
            <div className="flex items-center rounded-lg border border-stone-200 bg-stone-50 p-0.5 text-xs font-semibold">
              {[0.75, 1.0, 1.25].map((speed) => (
                <button
                  key={speed}
                  type="button"
                  onClick={() => handleSpeedChange(speed)}
                  className={`px-2 py-1 rounded-md transition-all cursor-pointer ${
                    playbackSpeed === speed
                      ? 'bg-white text-stone-900 shadow-2xs font-bold'
                      : 'text-stone-500 hover:text-stone-900'
                  }`}
                >
                  {speed}x
                </button>
              ))}
            </div>

            {/* Mute */}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                if (!videoRef.current) return;
                videoRef.current.muted = !isMuted;
                setIsMuted(!isMuted);
              }}
              title={isMuted ? 'Bật âm thanh' : 'Tắt âm thanh'}
              className="h-9 w-9 p-0 text-stone-500 hover:text-stone-900"
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
