'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { UserAppShell } from '@/components/layout/user-app-shell';
import { MaterialLessonList } from '@/components/materials/material-lesson-list';
import { materialsApi, userMaterialsApi } from '@/lib/api';
import { LearningMaterial, MaterialLesson, UserMaterialDetail } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, RotateCcw, CheckCircle2 } from 'lucide-react';

interface PageProps {
  params: Promise<{ materialId: string }>;
}

export default function MaterialDetailPage({ params }: PageProps) {
  const { materialId } = React.use(params);

  const [material, setMaterial] = useState<LearningMaterial | null>(null);
  const [lessons, setLessons] = useState<MaterialLesson[]>([]);
  const [userMaterial, setUserMaterial] = useState<UserMaterialDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // Auto enroll to ensure progress is tracked
      await materialsApi.enroll(materialId);

      const [materialRes, lessonsRes, userMatRes] = await Promise.allSettled([
        materialsApi.getMaterial(materialId),
        materialsApi.getLessons(materialId),
        userMaterialsApi.getMyMaterial(materialId),
      ]);

      if (materialRes.status === 'fulfilled' && materialRes.value) {
        setMaterial(materialRes.value);
      } else {
        setErrorMessage('Không tìm thấy tài liệu học tập.');
      }

      if (lessonsRes.status === 'fulfilled') {
        setLessons(lessonsRes.value);
      }

      if (userMatRes.status === 'fulfilled' && userMatRes.value) {
        setUserMaterial(userMatRes.value);
      }
    } catch (err: unknown) {
      console.error('Failed to load material detail:', err);
      setErrorMessage('Có lỗi xảy ra khi tải tài liệu học tập.');
    } finally {
      setIsLoading(false);
    }
  }, [materialId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const totalLessons = lessons.length;
  const completedLessons = userMaterial
    ? userMaterial.lessons.filter((l) => l.completed).length
    : 0;
  const progressPct =
    totalLessons > 0 ? Math.round((completedLessons / totalLessons) * 100) : 0;

  return (
    <UserAppShell>
      <div className="space-y-6 max-w-3xl mx-auto">
        {/* Back Link */}
        <div>
          <Link
            href="/materials"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-stone-500 hover:text-stone-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Quay lại kho tài liệu</span>
          </Link>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-32 w-full rounded-2xl" />
            <Skeleton className="h-16 w-full rounded-xl" />
            <Skeleton className="h-16 w-full rounded-xl" />
          </div>
        ) : errorMessage || !material ? (
          <div className="p-8 text-center bg-white rounded-2xl border border-stone-200 space-y-3">
            <p className="text-sm text-stone-600">{errorMessage || 'Không tìm thấy tài liệu này.'}</p>
            <Button variant="outline" size="sm" onClick={loadData} className="gap-1.5">
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Thử lại</span>
            </Button>
          </div>
        ) : (
          <>
            {/* Header / Summary Card */}
            <div className="p-6 rounded-2xl bg-white border border-stone-200/90 shadow-2xs space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  {material.level && (
                    <Badge variant="outline" className="font-semibold text-xs border-stone-200 bg-stone-50 text-stone-700">
                      JLPT {material.level}
                    </Badge>
                  )}
                  <Badge variant="secondary" className="text-xs uppercase font-medium text-stone-500">
                    {material.material_type || 'PDF'}
                  </Badge>
                </div>

                {progressPct >= 100 ? (
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

              <div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight">
                  {material.title}
                </h1>
                {material.description && (
                  <p className="text-xs sm:text-sm text-stone-500 mt-1 leading-relaxed">
                    {material.description}
                  </p>
                )}
              </div>

              {/* Progress info */}
              <div className="space-y-2 pt-2 border-t border-stone-100">
                <div className="flex items-center justify-between text-xs text-stone-600">
                  <span className="font-medium">
                    Tiến độ: <strong className="text-stone-900 font-bold">{completedLessons}</strong> / {totalLessons} bài học đã học
                  </span>
                  <span className="font-bold text-indigo-600 font-mono">
                    {progressPct}%
                  </span>
                </div>
                <Progress value={progressPct} className="h-2 rounded-full bg-stone-100" />
              </div>
            </div>

            {/* Lesson List */}
            <section aria-labelledby="lesson-list-heading" className="space-y-3">
              <h2
                id="lesson-list-heading"
                className="text-sm font-bold tracking-wider text-stone-600 uppercase"
              >
                Danh sách bài học ({totalLessons} bài)
              </h2>

              {lessons.length === 0 ? (
                <div className="p-8 text-center bg-white rounded-2xl border border-stone-200 text-stone-400 text-sm">
                  Chưa có bài học nào trong giáo trình này.
                </div>
              ) : (
                <MaterialLessonList
                  materialId={material.id}
                  lessons={lessons}
                  userLessons={userMaterial?.lessons}
                />
              )}
            </section>
          </>
        )}
      </div>
    </UserAppShell>
  );
}
