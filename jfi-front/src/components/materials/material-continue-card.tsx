'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { UserMaterial } from '@/types';
import { ArrowRight, CheckCircle2 } from 'lucide-react';

interface MaterialContinueCardProps {
  userMaterial: UserMaterial;
}

export function MaterialContinueCard({ userMaterial }: MaterialContinueCardProps) {
  const { material, progress, completed_lessons, total_lessons } = userMaterial;
  const progressPct = Math.round(progress);
  const isCompleted = completed_lessons > 0 && completed_lessons >= total_lessons;

  return (
    <Card className="border-stone-200/90 shadow-sm bg-white overflow-hidden rounded-2xl relative">
      <CardHeader className="pb-3 border-b border-stone-100/80">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-bold tracking-wider text-stone-500 uppercase">
            Tiếp tục học
          </span>

          <div className="flex items-center gap-1.5">
            {material.level && (
              <Badge variant="outline" className="font-semibold text-xs border-stone-200 bg-stone-50 text-stone-700">
                JLPT {material.level}
              </Badge>
            )}
            {isCompleted ? (
              <Badge variant="success" className="gap-1 text-xs">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Đã hoàn thành</span>
              </Badge>
            ) : (
              <Badge variant="subtle" className="text-xs">
                Đang học
              </Badge>
            )}
          </div>
        </div>

        <div className="pt-2">
          <h2 className="text-xl sm:text-2xl font-bold text-stone-900 tracking-tight">
            {material.title}
          </h2>
          {material.description && (
            <p className="text-xs sm:text-sm text-stone-500 mt-1 line-clamp-2 leading-relaxed">
              {material.description}
            </p>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-4 pb-5">
        <div className="flex items-center justify-between text-xs sm:text-sm">
          <span className="text-stone-600 font-medium">
            Tiến độ:{' '}
            <strong className="text-stone-900 font-bold text-sm sm:text-base">
              {completed_lessons}
            </strong>{' '}
            / {total_lessons} bài học
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
            ? 'Bạn đã hoàn thành tất cả các bài học trong giáo trình này'
            : 'Tiếp tục bài học đang dang dở từ lần trước'}
        </span>

        <Button asChild size="default" className="w-full sm:w-auto font-semibold px-6 gap-2 ml-auto shadow-xs">
          <Link href={`/materials/${material.id}`}>
            <span>Tiếp tục học</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
