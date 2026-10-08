'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { UserAppShell } from '@/components/layout/user-app-shell';
import { LessonReader } from '@/components/materials/lesson-reader';
import { materialsApi, userMaterialsApi } from '@/lib/api';
import { MaterialLesson, MaterialSection } from '@/types';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { ArrowLeft, RotateCcw } from 'lucide-react';

interface PageProps {
  params: Promise<{ materialId: string; lessonId: string }>;
}

export default function LessonReaderPage({ params }: PageProps) {
  const { materialId, lessonId } = React.use(params);

  const [lesson, setLesson] = useState<MaterialLesson | null>(null);
  const [sections, setSections] = useState<MaterialSection[]>([]);
  const [allLessons, setAllLessons] = useState<MaterialLesson[]>([]);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [lessonRes, sectionsRes, allLessonsRes, userMatRes] =
        await Promise.allSettled([
          materialsApi.getLessonDetail(materialId, lessonId),
          materialsApi.getLessonSections(materialId, lessonId),
          materialsApi.getLessons(materialId),
          userMaterialsApi.getMyMaterial(materialId),
        ]);

      if (lessonRes.status === 'fulfilled' && lessonRes.value) {
        setLesson(lessonRes.value);
      } else {
        setErrorMessage('Không tìm thấy thông tin bài học.');
      }

      if (sectionsRes.status === 'fulfilled') {
        setSections(sectionsRes.value);
      }

      if (allLessonsRes.status === 'fulfilled') {
        setAllLessons(allLessonsRes.value);
      }

      if (userMatRes.status === 'fulfilled' && userMatRes.value) {
        const found = userMatRes.value.lessons.find((l) => l.lesson_id === lessonId);
        if (found) {
          setIsCompleted(found.completed);
        }
      }
    } catch (err: unknown) {
      console.error('Failed to load lesson reader:', err);
      setErrorMessage('Không thể tải nội dung bài học.');
    } finally {
      setIsLoading(false);
    }
  }, [materialId, lessonId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Find prev and next lesson
  const sorted = [...allLessons].sort((a, b) => a.lesson_number - b.lesson_number);
  const currentIndex = sorted.findIndex((l) => l.id === lessonId);
  const prevLesson = currentIndex > 0 ? sorted[currentIndex - 1] : null;
  const nextLesson = currentIndex !== -1 && currentIndex < sorted.length - 1 ? sorted[currentIndex + 1] : null;

  return (
    <UserAppShell>
      <div className="space-y-6 max-w-3xl mx-auto">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between gap-4">
          <Link
            href={`/materials/${materialId}`}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-stone-500 hover:text-stone-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Quay lại danh sách bài học</span>
          </Link>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="space-y-6 py-4">
            <Skeleton className="h-10 w-2/3 rounded-xl" />
            <Skeleton className="h-4 w-1/3 rounded-lg" />
            <div className="space-y-4 pt-4">
              <Skeleton className="h-28 w-full rounded-2xl" />
              <Skeleton className="h-36 w-full rounded-2xl" />
              <Skeleton className="h-24 w-full rounded-2xl" />
            </div>
          </div>
        ) : errorMessage || !lesson ? (
          <div className="p-8 text-center bg-white rounded-2xl border border-stone-200 space-y-3">
            <p className="text-sm text-stone-600">{errorMessage || 'Không tìm thấy bài học này.'}</p>
            <Button variant="outline" size="sm" onClick={loadData} className="gap-1.5">
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Thử lại</span>
            </Button>
          </div>
        ) : (
          <LessonReader
            materialId={materialId}
            lesson={lesson}
            sections={sections}
            prevLessonId={prevLesson?.id}
            nextLessonId={nextLesson?.id}
            initialCompleted={isCompleted}
            onCompletedChange={(val) => setIsCompleted(val)}
          />
        )}
      </div>
    </UserAppShell>
  );
}
