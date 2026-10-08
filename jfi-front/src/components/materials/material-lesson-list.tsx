'use client';

import React from 'react';
import Link from 'next/link';
import { MaterialLesson, UserMaterialLesson } from '@/types';
import { CheckCircle2, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MaterialLessonListProps {
  materialId: string;
  lessons: MaterialLesson[];
  userLessons?: UserMaterialLesson[];
}

export function MaterialLessonList({ materialId, lessons, userLessons = [] }: MaterialLessonListProps) {
  const completionMap = new Map<string, boolean>();
  userLessons.forEach((ul) => {
    completionMap.set(ul.lesson_id, ul.completed);
  });

  // Find first uncompleted lesson as the "current" lesson
  const currentLessonIndex = lessons.findIndex((l) => {
    const isCompleted = l.is_completed || completionMap.get(l.id) === true;
    return !isCompleted;
  });

  return (
    <div className="space-y-2">
      {lessons.map((lesson, idx) => {
        const isCompleted = lesson.is_completed || completionMap.get(lesson.id) === true;
        const isCurrent = idx === (currentLessonIndex === -1 ? 0 : currentLessonIndex);

        return (
          <Link
            key={lesson.id}
            href={`/materials/${materialId}/lessons/${lesson.id}`}
            className={cn(
              'group flex items-center justify-between p-4 rounded-xl border transition-all',
              isCurrent
                ? 'border-indigo-200 bg-indigo-50/40 hover:bg-indigo-50/70 shadow-2xs'
                : 'border-stone-200/80 bg-white hover:bg-stone-50/80'
            )}
          >
            <div className="flex items-center gap-3.5 min-w-0">
              <div
                className={cn(
                  'w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs shrink-0',
                  isCompleted
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                    : isCurrent
                      ? 'bg-indigo-600 text-white shadow-2xs'
                      : 'bg-stone-100 text-stone-600'
                )}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : (
                  <span>{lesson.lesson_number}</span>
                )}
              </div>

              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-stone-500">
                    Bài {lesson.lesson_number}
                  </span>
                  {isCurrent && !isCompleted && (
                    <span className="text-[10px] font-semibold text-indigo-700 bg-indigo-100/80 px-2 py-0.5 rounded-full">
                      Đang học
                    </span>
                  )}
                  {isCompleted && (
                    <span className="text-[10px] font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded-md">
                      Đã hoàn thành
                    </span>
                  )}
                </div>
                <h4 className="text-sm font-bold text-stone-900 group-hover:text-indigo-600 transition-colors truncate">
                  {lesson.title || `Bài học số ${lesson.lesson_number}`}
                </h4>
                {lesson.description && (
                  <p className="text-xs text-stone-400 truncate mt-0.5">
                    {lesson.description}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0 ml-3 text-stone-400 group-hover:text-stone-700 transition-colors">
              {lesson.page_start && (
                <span className="text-[11px] text-stone-400 hidden sm:inline">
                  trang {lesson.page_start}{lesson.page_end ? `-${lesson.page_end}` : ''}
                </span>
              )}
              <ChevronRight className="w-4 h-4" />
            </div>
          </Link>
        );
      })}
    </div>
  );
}
