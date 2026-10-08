'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { TodayStudyState } from '@/types';
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  Sparkles,
} from 'lucide-react';

interface TodayStudyCardProps {
  studyState?: TodayStudyState;
  isLoading?: boolean;
}

export function TodayStudyCard({ studyState, isLoading }: TodayStudyCardProps) {
  if (isLoading) {
    return (
      <Card className="border-stone-200/90 shadow-sm p-6 space-y-4 bg-white rounded-2xl">
        <div className="flex items-center justify-between">
          <Skeleton className="h-7 w-32" />
          <Skeleton className="h-6 w-24" />
        </div>
        <Skeleton className="h-2.5 w-full rounded-full" />
        <div className="flex justify-between items-center">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-16" />
        </div>
        <div className="flex justify-end pt-2">
          <Skeleton className="h-10 w-36 rounded-xl" />
        </div>
      </Card>
    );
  }

  if (!studyState?.hasActivePlan || !studyState.plan) {
    return null;
  }

  const { plan, day, progress } = studyState;
  const dayNumber = day?.day_number || 1;
  const totalItems = progress?.total || 0;
  const learnedItems = progress?.learned || 0;
  const percentage = progress?.percentage !== undefined ? Math.round(progress.percentage) : 0;
  const isCompleted = Boolean(progress?.completed || (totalItems > 0 && learnedItems >= totalItems));

  const studyDayHref = day ? `/study?plan=${plan.id}&day=${day.id}` : '/study';

  // 1. When total assignments = 0: Show meaningful empty/rest state (NO 0/0 and NO 100% bar)
  if (totalItems === 0) {
    return (
      <Card className="border-stone-200/90 shadow-sm bg-white overflow-hidden rounded-2xl">
        <CardHeader className="pb-3 border-b border-stone-100/80">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-stone-900 tracking-tight">
                今日の学習
              </h2>
              <p className="text-xs text-stone-500 mt-0.5">
                本日の学習目標と進捗
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-stone-100 text-stone-700 font-semibold text-xs border border-stone-200/60">
                Day {dayNumber} / {plan.total_days || 30}
              </span>
              <Badge
                variant="outline"
                className="text-xs font-semibold px-2 py-0.5 border-stone-200 bg-white text-stone-600"
              >
                JLPT {plan.level}
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="py-5 sm:py-6 space-y-2">
          <div className="flex items-start gap-3.5 p-4 rounded-xl bg-stone-50/80 border border-stone-200/60">
            <div className="p-2 rounded-lg bg-white border border-stone-200 text-stone-600 shrink-0">
              <Sparkles className="w-5 h-5 text-indigo-500" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-stone-900">
                本日の割り当てはありません
              </h3>
              <p className="text-xs text-stone-500 leading-relaxed">
                この日は新しい単語・文法の新規割り当てがありません。これまでに学んだ内容の復習や、Shadowing動画での練習を進めましょう。
              </p>
            </div>
          </div>
        </CardContent>

        <CardFooter className="pt-3 pb-4 px-6 border-t border-stone-100/90 bg-stone-50/40 flex items-center justify-between gap-4">
          <span className="text-xs text-stone-500 truncate hidden sm:block">
            計画全体のスケジュールや他日程の内容を確認できます
          </span>
          <Button
            asChild
            variant="outline"
            size="sm"
            className="w-full sm:w-auto font-medium gap-1.5 border-stone-200 hover:bg-stone-100 ml-auto"
          >
            <Link href={studyDayHref}>
              <span>学習計画を見る</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </Button>
        </CardFooter>
      </Card>
    );
  }

  // 2. Normal State: When totalItems > 0
  return (
    <Card className="border-stone-200/90 shadow-sm bg-white overflow-hidden rounded-2xl relative">
      <CardHeader className="pb-3 border-b border-stone-100/80">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-stone-900 tracking-tight">
              今日の学習
            </h2>
            <p className="text-xs text-stone-500 mt-0.5">
              本日の学習目標と進捗
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-stone-100 text-stone-700 font-semibold text-xs border border-stone-200/60">
              Day {dayNumber} / {plan.total_days || 30}
            </span>
            <Badge
              variant="outline"
              className="text-xs font-semibold px-2 py-0.5 border-stone-200 bg-white text-stone-600"
            >
              JLPT {plan.level}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 pt-4 pb-5">
        {/* Progress Bar & Percentage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs sm:text-sm">
            <div className="flex items-center gap-1.5 font-medium text-stone-600">
              <span>進捗:</span>
              <strong className="text-stone-900 font-bold text-sm sm:text-base">
                {learnedItems}
              </strong>
              <span className="text-stone-400">/</span>
              <span>{totalItems} 項目</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="font-bold text-indigo-600 font-mono text-sm sm:text-base">
                {percentage}%
              </span>

              {isCompleted ? (
                <Badge variant="success" className="gap-1 text-[11px] font-medium py-0 px-2">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>完了</span>
                </Badge>
              ) : learnedItems > 0 ? (
                <Badge variant="subtle" className="gap-1 text-[11px] font-medium py-0 px-2">
                  <Clock className="w-3 h-3" />
                  <span>学習中</span>
                </Badge>
              ) : (
                <Badge variant="secondary" className="text-[11px] font-medium py-0 px-2 text-stone-500">
                  <span>未着手</span>
                </Badge>
              )}
            </div>
          </div>

          <Progress value={percentage} className="h-2.5 rounded-full bg-stone-100" />
        </div>
      </CardContent>

      {/* Primary Continue CTA */}
      <CardFooter className="pt-3 pb-4 px-6 border-t border-stone-100/90 bg-stone-50/40 flex items-center justify-between gap-4">
        <div className="text-xs text-stone-500 truncate hidden sm:block">
          {isCompleted
            ? '本日の学習目標を達成しました。'
            : '本日の割り当て内容を学習しましょう。'}
        </div>

        <Button asChild size="default" className="w-full sm:w-auto font-semibold px-5 gap-2 ml-auto shadow-xs">
          <Link href={studyDayHref}>
            <span>{isCompleted ? '学習内容を確認' : '学習を続ける'}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
