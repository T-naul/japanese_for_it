'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { UserAppShell } from '@/components/layout/user-app-shell';
import { ShadowingVideoCard } from '@/components/shadowing/shadowing-video-card';
import { ShadowingContinueCard } from '@/components/shadowing/shadowing-continue-card';
import { shadowingApi, userShadowingApi } from '@/lib/api';
import { ShadowingVideo, UserShadowingVideo, JLPTLevel } from '@/types';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { RotateCcw, Video } from 'lucide-react';

const JLPT_LEVELS: (JLPTLevel | 'ALL')[] = ['ALL', 'N5', 'N4', 'N3', 'N2', 'N1'];

export default function VideoLibraryPage() {
  const [videos, setVideos] = useState<ShadowingVideo[]>([]);
  const [userVideos, setUserVideos] = useState<UserShadowingVideo[]>([]);
  const [selectedLevel, setSelectedLevel] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [videosRes, userVideosRes] = await Promise.allSettled([
        shadowingApi.getVideos(selectedLevel !== 'ALL' ? { level: selectedLevel } : undefined),
        userShadowingApi.getMyShadowing(),
      ]);

      if (videosRes.status === 'fulfilled') {
        setVideos(videosRes.value);
      } else {
        console.warn('Failed to load shadowing videos:', videosRes.reason);
      }

      if (userVideosRes.status === 'fulfilled') {
        setUserVideos(userVideosRes.value);
      }
    } catch (err: unknown) {
      console.error('Failed to load video library data:', err);
      setErrorMessage('Không thể tải danh sách video luyện tập.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedLevel]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Find map of userVideos by video id
  const userVideoMap = new Map<string, UserShadowingVideo>();
  userVideos.forEach((uv) => {
    userVideoMap.set(uv.video_id, uv);
  });

  // Active continue video: First video with percentage < 100 or recently enrolled
  const activeUserVideo = userVideos.find((uv) => uv.percentage < 100) || userVideos[0];

  return (
    <UserAppShell>
      <div className="space-y-8 max-w-4xl mx-auto">
        {/* Header */}
        <header className="space-y-1">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight">
            Luyện nói Shadowing
          </h1>
          <p className="text-xs sm:text-sm text-stone-500">
            Luyện nghe, nói theo ngữ điệu và phản xạ tiếng Nhật IT tự nhiên.
          </p>
        </header>

        {/* Loading Skeletons */}
        {isLoading ? (
          <div className="space-y-6">
            <Skeleton className="h-44 w-full rounded-2xl" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Skeleton className="h-48 rounded-2xl" />
              <Skeleton className="h-48 rounded-2xl" />
            </div>
          </div>
        ) : errorMessage ? (
          <div className="p-8 text-center bg-white rounded-2xl border border-stone-200 space-y-3">
            <p className="text-sm text-stone-600">{errorMessage}</p>
            <Button variant="outline" size="sm" onClick={loadData} className="gap-1.5">
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Thử lại</span>
            </Button>
          </div>
        ) : (
          <>
            {/* 1. Active / Continue Shadowing */}
            {activeUserVideo && (
              <section aria-labelledby="continue-video-heading">
                <ShadowingContinueCard userVideo={activeUserVideo} />
              </section>
            )}

            {/* 2. Video Library */}
            <section aria-labelledby="video-library-heading" className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <h2
                  id="video-library-heading"
                  className="text-base font-bold text-stone-900 tracking-tight"
                >
                  Kho video luyện tập
                </h2>

                {/* JLPT Level Filters */}
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
                  {JLPT_LEVELS.map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => setSelectedLevel(lvl)}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                        selectedLevel === lvl
                          ? 'bg-stone-900 text-white shadow-2xs'
                          : 'bg-stone-100 text-stone-600 hover:bg-stone-200/70'
                      }`}
                    >
                      {lvl === 'ALL' ? 'Tất cả' : lvl}
                    </button>
                  ))}
                </div>
              </div>

              {videos.length === 0 ? (
                <div className="p-12 text-center bg-white rounded-2xl border border-stone-200 space-y-3">
                  <div className="w-12 h-12 rounded-xl bg-stone-100 text-stone-400 flex items-center justify-center mx-auto">
                    <Video className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-stone-900">
                      Chưa có video luyện tập
                    </h3>
                    <p className="text-xs text-stone-500 mt-1">
                      Hiện chưa có video luyện Shadowing nào khả dụng. Vui lòng quay lại sau.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {videos.map((v) => (
                    <ShadowingVideoCard
                      key={v.id}
                      video={v}
                      userVideo={userVideoMap.get(v.id)}
                    />
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </UserAppShell>
  );
}
