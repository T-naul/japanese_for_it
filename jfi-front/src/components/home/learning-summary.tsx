'use client';

import React from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { BookOpen, FileText, BookmarkCheck, Video, ArrowRight } from 'lucide-react';

interface LearningSummaryProps {
  vocabLearned?: number;
  grammarLearned?: number;
  reviewAvailable?: number;
  shadowingEnrolled?: number;
  materialsEnrolled?: number;
}

export function LearningSummary({
  vocabLearned = 0,
  grammarLearned = 0,
  reviewAvailable = 0,
  shadowingEnrolled = 0,
}: LearningSummaryProps) {
  const hasActivity = vocabLearned > 0 || grammarLearned > 0 || shadowingEnrolled > 0;

  return (
    <section className="space-y-3.5 my-8">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold uppercase tracking-wider text-stone-500">
          Tổng quan tiến độ
        </h3>
        <Link
          href="/progress"
          className="text-xs text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
        >
          <span>Xem chi tiết</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Metric 1: Vocabulary */}
        <div className="p-4 rounded-2xl bg-white border border-stone-200/80 shadow-2xs">
          <div className="flex items-center gap-2 text-stone-500 text-xs mb-2 font-medium">
            <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
            <span>Từ vựng đã học</span>
          </div>
          <div className="text-2xl font-bold text-stone-900 font-mono">
            {vocabLearned}
          </div>
          <div className="text-[11px] text-stone-400 mt-0.5">từ vựng IT</div>
        </div>

        {/* Metric 2: Grammar */}
        <div className="p-4 rounded-2xl bg-white border border-stone-200/80 shadow-2xs">
          <div className="flex items-center gap-2 text-stone-500 text-xs mb-2 font-medium">
            <FileText className="w-3.5 h-3.5 text-violet-600" />
            <span>Ngữ pháp đã học</span>
          </div>
          <div className="text-2xl font-bold text-stone-900 font-mono">
            {grammarLearned}
          </div>
          <div className="text-[11px] text-stone-400 mt-0.5">mẫu câu cấu trúc</div>
        </div>

        {/* Metric 3: Review */}
        <div className="p-4 rounded-2xl bg-white border border-stone-200/80 shadow-2xs">
          <div className="flex items-center gap-2 text-stone-500 text-xs mb-2 font-medium">
            <BookmarkCheck className="w-3.5 h-3.5 text-amber-500" />
            <span>Cần ôn tập</span>
          </div>
          <div className="text-2xl font-bold text-stone-900 font-mono">
            {reviewAvailable}
          </div>
          <div className="text-[11px] text-stone-400 mt-0.5">mục tới hạn SRS</div>
        </div>

        {/* Metric 4: Shadowing */}
        <div className="p-4 rounded-2xl bg-white border border-stone-200/80 shadow-2xs">
          <div className="flex items-center gap-2 text-stone-500 text-xs mb-2 font-medium">
            <Video className="w-3.5 h-3.5 text-emerald-600" />
            <span>Video Shadowing</span>
          </div>
          <div className="text-2xl font-bold text-stone-900 font-mono">
            {shadowingEnrolled}
          </div>
          <div className="text-[11px] text-stone-400 mt-0.5">bài đang luyện</div>
        </div>
      </div>

      {!hasActivity && (
        <p className="text-xs text-stone-400 text-center pt-1">
          Bắt đầu học bài đầu tiên hôm nay để tích lũy thống kê tiến độ cá nhân của bạn.
        </p>
      )}
    </section>
  );
}
