'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ShadowingVideo, UserShadowingVideo } from '@/types';
import { Video, ArrowRight, CheckCircle2, Clock } from 'lucide-react';

interface ShadowingVideoCardProps {
  video: ShadowingVideo;
  userVideo?: UserShadowingVideo | null;
}

function formatDuration(seconds?: number): string {
  if (!seconds || seconds <= 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

export function ShadowingVideoCard({ video, userVideo }: ShadowingVideoCardProps) {
  const isEnrolled = !!userVideo;
  const isReady = video.status === 'ready';

  const progress = userVideo ? Math.round(userVideo.percentage) : 0;
  const completedSegments = userVideo?.completed_segments || 0;
  const totalSegments = userVideo?.total_segments || 0;

  return (
    <Card className="border-stone-200/90 bg-white shadow-2xs hover:border-stone-300 transition-all rounded-2xl flex flex-col justify-between overflow-hidden">
      <CardHeader className="p-5 pb-3">
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-1.5">
            {video.level && (
              <Badge variant="outline" className="font-semibold text-xs border-stone-200 bg-stone-50 text-stone-700">
                JLPT {video.level}
              </Badge>
            )}
            {video.duration_seconds && video.duration_seconds > 0 ? (
              <span className="text-xs text-stone-400 flex items-center gap-1 font-mono">
                <Clock className="w-3.5 h-3.5" />
                {formatDuration(video.duration_seconds)}
              </span>
            ) : null}
          </div>

          <div>
            {isEnrolled && progress >= 100 ? (
              <Badge variant="success" className="gap-1 text-[11px]">
                <CheckCircle2 className="w-3 h-3" />
                <span>Hoàn thành</span>
              </Badge>
            ) : isEnrolled ? (
              <Badge variant="subtle" className="text-[11px]">
                Đang luyện
              </Badge>
            ) : (
              <Badge variant="outline" className="text-[11px] text-stone-500">
                Chưa luyện
              </Badge>
            )}
          </div>
        </div>

        {/* Video Thumbnail Placeholder or preview */}
        <div className="w-full h-36 rounded-xl bg-stone-900 text-white flex items-center justify-center relative overflow-hidden mb-3 group">
          <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center text-white shadow-md">
            <Video className="w-6 h-6 text-white" />
          </div>
          <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-stone-950/80 text-[11px] font-mono text-stone-200">
            {formatDuration(video.duration_seconds)}
          </span>
        </div>

        <h3 className="text-base font-bold text-stone-900 tracking-tight line-clamp-2">
          {video.title}
        </h3>

        {video.description && (
          <p className="text-xs text-stone-500 line-clamp-2 mt-1 leading-relaxed">
            {video.description}
          </p>
        )}
      </CardHeader>

      <CardContent className="px-5 py-2">
        {/* Progress if enrolled */}
        {isEnrolled && totalSegments > 0 ? (
          <div className="space-y-1.5 pt-1">
            <div className="flex items-center justify-between text-xs text-stone-500">
              <span>
                Tiến độ: <strong className="text-stone-800 font-semibold">{completedSegments}</strong> / {totalSegments} câu
              </span>
              <span className="font-bold text-indigo-600 font-mono">{progress}%</span>
            </div>
            <Progress value={progress} className="h-1.5 rounded-full bg-stone-100" />
          </div>
        ) : null}
      </CardContent>

      <CardFooter className="p-5 pt-3 border-t border-stone-100 bg-stone-50/40">
        {isReady ? (
          <Button
            asChild
            variant={isEnrolled ? 'default' : 'outline'}
            size="sm"
            className="w-full justify-between font-semibold"
          >
            <Link href={`/video/${video.id}`}>
              <span>{isEnrolled ? 'Tiếp tục luyện tập' : 'Bắt đầu luyện tập'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </Button>
        ) : (
          <Button disabled size="sm" variant="ghost" className="w-full text-xs text-stone-400">
            <span>Video đang được xử lý...</span>
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
