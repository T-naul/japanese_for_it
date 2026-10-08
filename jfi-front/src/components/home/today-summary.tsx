'use client';

import React from 'react';
import { Card } from '@/components/ui/card';
import { StudyPlanDayProgress } from '@/types';

interface TodaySummaryProps {
  progress?: StudyPlanDayProgress;
  shadowingCount?: number;
}

export function TodaySummary({ progress, shadowingCount = 0 }: TodaySummaryProps) {
  if (!progress) return null;

  const vocabCount = progress.vocabulary?.learned || 0;
  const grammarCount = progress.grammar?.learned || 0;
  const totalActivity = vocabCount + grammarCount + shadowingCount;

  // 4. Hide Today Summary when all values are zero
  if (totalActivity === 0) {
    return null;
  }

  return (
    <section aria-labelledby="today-summary-heading" className="space-y-2.5 pt-1">
      <h3
        id="today-summary-heading"
        className="text-xs font-semibold tracking-wider text-stone-500 uppercase"
      >
        Kết quả học tập hôm nay
      </h3>

      <Card className="border-stone-200/80 bg-white shadow-2xs p-4 sm:p-5 rounded-xl">
        <div className="grid grid-cols-3 divide-x divide-stone-100 text-center">
          <div className="px-2">
            <div className="text-xs text-stone-500 font-medium">Từ vựng</div>
            <div className="text-lg sm:text-xl font-bold text-stone-900 mt-1 font-mono">
              {vocabCount}
            </div>
          </div>

          <div className="px-2">
            <div className="text-xs text-stone-500 font-medium">Ngữ pháp</div>
            <div className="text-lg sm:text-xl font-bold text-stone-900 mt-1 font-mono">
              {grammarCount}
            </div>
          </div>

          <div className="px-2">
            <div className="text-xs text-stone-500 font-medium">Luyện nhại</div>
            <div className="text-lg sm:text-xl font-bold text-stone-900 mt-1 font-mono">
              {shadowingCount}
            </div>
          </div>
        </div>
      </Card>
    </section>
  );
}
