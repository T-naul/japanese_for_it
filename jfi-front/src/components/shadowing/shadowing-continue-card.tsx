'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { UserShadowingVideo } from '@/types';
import { ArrowRight, CheckCircle2 } from 'lucide-react';

interface ShadowingContinueCardProps {
  userVideo: UserShadowingVideo;
}

export function ShadowingContinueCard({ userVideo }: ShadowingContinueCardProps) {
  const { video_id, title, level, completed_segments, total_segments, percentage } = userVideo;
  const progressPct = Math.round(percentage);
  const isCompleted = completed_segments > 0 && completed_segments >= total_segments;

  return (
    <Card className="border-stone-200/90 shadow-sm bg-white overflow-hidden rounded-2xl relative">
      <CardHeader className="pb-3 border-b border-stone-100/80">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-bold tracking-wider text-stone-500 uppercase">
            Tiếp tục luyện tập
          </span>

          <div className="flex items-center gap-1.5">
            {level && (
              <Badge variant="outline" className="font-semibold text-xs border-stone-200 bg-stone-50 text-stone-700">
                JLPT {level}
              </Badge>
            )}
            {isCompleted ? (
              <Badge variant="success" className="gap-1 text-xs">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Hoàn thành</span>
              </Badge>
            ) : (
              <Badge variant="subtle" className="text-xs">
                Đang luyện
              </Badge>
            )}
          </div>
        </div>

        <div className="pt-2">
          <h2 className="text-xl sm:text-2xl font-bold text-stone-900 tracking-tight">
            {title}
          </h2>
          <p className="text-xs sm:text-sm text-stone-500 mt-1">
            Luyện nghe và nói theo ngữ điệu tự nhiên của người bản xứ trong ngữ cảnh IT.
          </p>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-4 pb-5">
        <div className="flex items-center justify-between text-xs sm:text-sm">
          <span className="text-stone-600 font-medium">
            Tiến độ:{' '}
            <strong className="text-stone-900 font-bold text-sm sm:text-base">
              {completed_segments}
            </strong>{' '}
            / {total_segments} câu thoại
          </span>
          <span className="font-bold text-indigo-600 font-mono text-sm sm:text-base">
            {progressPct}%
          </span>
        </div>

        <Progress value={progressPct} className="h-2.5 rounded-full bg-stone-100" />
      </CardContent>

      <CardFooter className="pt-3 pb-4 px-6 border-t border-stone-100/90 bg-stone-50/40 flex items-center justify-between gap-4">
        <span className="text-xs text-stone-500 hidden sm:block truncate">
          {isCompleted
            ? 'Bạn đã hoàn thành tất cả các câu thoại trong video này'
            : 'Tiếp tục luyện tập câu thoại tiếp theo'}
        </span>

        <Button asChild size="default" className="w-full sm:w-auto font-semibold px-6 gap-2 ml-auto shadow-xs">
          <Link href={`/video/${video_id}`}>
            <span>Tiếp tục luyện tập</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
