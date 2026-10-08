'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Link from 'next/link';
import { UserAppShell } from '@/components/layout/user-app-shell';
import { ShadowingVideoPlayer } from '@/components/shadowing/shadowing-video-player';
import { ShadowingSentence } from '@/components/shadowing/shadowing-sentence';
import { ShadowingSegmentList } from '@/components/shadowing/shadowing-segment-list';
import { shadowingApi, userShadowingApi } from '@/lib/api';
import {
  ShadowingVideo,
  ShadowingSegment,
  UserShadowingDetail,
} from '@/types';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  ArrowLeft,
  RotateCcw,
  CheckCircle2,
  Loader2,
} from 'lucide-react';

interface PageProps {
  params: Promise<{ videoId: string }>;
}

export default function VideoPracticePage({ params }: PageProps) {
  const { videoId } = React.use(params);

  const [video, setVideo] = useState<ShadowingVideo | null>(null);
  const [segments, setSegments] = useState<ShadowingSegment[]>([]);
  const [userVideo, setUserVideo] = useState<UserShadowingDetail | null>(null);
  const [currentSegment, setCurrentSegment] = useState<ShadowingSegment | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isCompleting, setIsCompleting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // Auto enroll into video
      await shadowingApi.enroll(videoId);

      const [videoRes, segmentsRes, userVideoRes] = await Promise.allSettled([
        shadowingApi.getVideo(videoId),
        shadowingApi.getVideoSegments(videoId),
        userShadowingApi.getMyShadowingVideo(videoId),
      ]);

      if (videoRes.status === 'fulfilled' && videoRes.value) {
        setVideo(videoRes.value);
      } else {
        setErrorMessage('Không tìm thấy thông tin video này.');
      }

      let loadedSegments: ShadowingSegment[] = [];
      if (segmentsRes.status === 'fulfilled') {
        loadedSegments = [...segmentsRes.value].sort((a, b) => a.sequence - b.sequence);
        setSegments(loadedSegments);
      }

      if (userVideoRes.status === 'fulfilled' && userVideoRes.value) {
        setUserVideo(userVideoRes.value);
      }

      // Determine initial segment: First uncompleted or first segment
      if (loadedSegments.length > 0) {
        let initialSeg = loadedSegments[0];
        if (userVideoRes.status === 'fulfilled' && userVideoRes.value) {
          const completedSet = new Set(
            userVideoRes.value.segments.filter((s) => s.is_completed).map((s) => s.sequence)
          );
          const firstUncompleted = loadedSegments.find((s) => !completedSet.has(s.sequence));
          if (firstUncompleted) initialSeg = firstUncompleted;
        }
        setCurrentSegment(initialSeg);
      }
    } catch (err: unknown) {
      console.error('Failed to load video practice room:', err);
      setErrorMessage('Có lỗi xảy ra khi tải phòng luyện tập video.');
    } finally {
      setIsLoading(false);
    }
  }, [videoId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // When video playback time updates, synchronize current segment
  const handleTimeUpdate = (currentTime: number) => {
    if (!segments || segments.length === 0) return;
    const matching = segments.find(
      (s) => currentTime >= s.start_time && currentTime <= s.end_time
    );
    if (matching && matching.id !== currentSegment?.id) {
      setCurrentSegment(matching);
    }
  };

  // Mark current segment completed
  const handleCompleteSegment = async () => {
    if (!currentSegment) return;
    setIsCompleting(true);
    try {
      const res = await userShadowingApi.completeSegment(videoId, currentSegment.id);
      if (res) {
        // Refresh or update state
        setUserVideo((prev) => {
          if (!prev) return null;
          const updatedSegments = prev.segments.map((s) =>
            s.sequence === currentSegment.sequence ? { ...s, is_completed: true } : s
          );
          return {
            ...prev,
            progress: {
              completed_segments: res.completed_segments,
              total_segments: res.total_segments,
              percentage: res.percentage,
              completed: res.video_status === 'completed',
            },
            segments: updatedSegments,
          };
        });
      }
    } catch (err: unknown) {
      console.error('Failed to complete segment:', err);
    } finally {
      setIsCompleting(false);
    }
  };

  const totalSegments = segments.length;
  const completedSegments = userVideo?.progress?.completed_segments || 0;
  const progressPct = totalSegments > 0 ? Math.round(userVideo?.progress?.percentage || 0) : 0;
  const isAllCompleted = totalSegments > 0 && completedSegments >= totalSegments;

  const isCurrentCompleted = useMemo(() => {
    if (!currentSegment || !userVideo) return false;
    const found = userVideo.segments.find((s) => s.sequence === currentSegment.sequence);
    return found ? found.is_completed : false;
  }, [currentSegment, userVideo]);

  return (
    <UserAppShell>
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between gap-4">
          <Link
            href="/video"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-stone-500 hover:text-stone-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Quay lại kho video</span>
          </Link>
        </div>

        {isLoading ? (
          <div className="space-y-6">
            <Skeleton className="h-64 w-full rounded-2xl" />
            <Skeleton className="h-28 w-full rounded-2xl" />
            <Skeleton className="h-44 w-full rounded-2xl" />
          </div>
        ) : errorMessage || !video ? (
          <div className="p-8 text-center bg-white rounded-2xl border border-stone-200 space-y-3">
            <p className="text-sm text-stone-600">{errorMessage || 'Không tìm thấy video này.'}</p>
            <Button variant="outline" size="sm" onClick={loadData} className="gap-1.5">
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Thử lại</span>
            </Button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Header info */}
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  {video.level && (
                    <Badge variant="outline" className="font-semibold text-xs border-stone-200 bg-stone-50 text-stone-700">
                      JLPT {video.level}
                    </Badge>
                  )}
                  {isAllCompleted ? (
                    <Badge variant="success" className="gap-1 text-xs">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Đã hoàn thành</span>
                    </Badge>
                  ) : (
                    <Badge variant="subtle" className="text-xs">
                      Đang luyện tập
                    </Badge>
                  )}
                </div>

                <h1 className="text-xl sm:text-2xl font-extrabold text-stone-900 tracking-tight">
                  {video.title}
                </h1>
              </div>

              {/* Overall Progress Counter */}
              {totalSegments > 0 && (
                <div className="text-right">
                  <div className="text-xs text-stone-500">
                    Tiến độ: <strong className="text-stone-900">{completedSegments}</strong> / {totalSegments} câu
                  </div>
                  <div className="text-sm font-bold text-indigo-600 font-mono">
                    {progressPct}%
                  </div>
                </div>
              )}
            </div>

            {/* Video Player */}
            <ShadowingVideoPlayer
              videoUrl={video.video_url}
              segments={segments}
              currentSegment={currentSegment}
              onSelectSegment={(seg) => setCurrentSegment(seg)}
              onTimeUpdate={handleTimeUpdate}
            />

            {/* Current Sentence Display */}
            <ShadowingSentence
              segment={currentSegment}
              totalSegments={totalSegments}
              onReplay={() => {
                if (currentSegment) setCurrentSegment({ ...currentSegment });
              }}
            />

            {/* Segment Completion Action */}
            {currentSegment && (
              <div className="p-4 rounded-xl bg-white border border-stone-200 shadow-2xs flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="text-xs text-stone-500 text-center sm:text-left">
                  {isCurrentCompleted
                    ? 'Bạn đã hoàn thành luyện tập câu thoại này.'
                    : 'Nói theo ngữ điệu video cho đến khi tự tin, sau đó bấm xác nhận hoàn thành.'}
                </div>

                <Button
                  onClick={handleCompleteSegment}
                  disabled={isCompleting}
                  variant={isCurrentCompleted ? 'outline' : 'default'}
                  size="sm"
                  className="w-full sm:w-auto font-semibold gap-1.5 shadow-xs"
                >
                  {isCompleting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Đang lưu...</span>
                    </>
                  ) : isCurrentCompleted ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Đã hoàn thành câu này</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Đánh dấu câu này đã xong</span>
                    </>
                  )}
                </Button>
              </div>
            )}

            {/* Segment List Section */}
            <section aria-labelledby="segment-list-heading" className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <h2
                  id="segment-list-heading"
                  className="text-xs font-bold tracking-wider text-stone-600 uppercase"
                >
                  Danh sách câu thoại ({totalSegments} câu)
                </h2>
                <span className="text-xs text-stone-400">
                  Nhấn vào câu bất kỳ để phát đoạn tương ứng
                </span>
              </div>

              <ShadowingSegmentList
                segments={segments}
                currentSegment={currentSegment}
                userSegments={userVideo?.segments}
                onSelectSegment={(seg) => setCurrentSegment(seg)}
              />
            </section>
          </div>
        )}
      </div>
    </UserAppShell>
  );
}
