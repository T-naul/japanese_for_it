'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { UserAppShell } from '@/components/layout/user-app-shell';
import { MaterialCard } from '@/components/materials/material-card';
import { MaterialContinueCard } from '@/components/materials/material-continue-card';
import { materialsApi, userMaterialsApi } from '@/lib/api';
import { LearningMaterial, UserMaterial, JLPTLevel } from '@/types';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { RotateCcw, FolderOpen } from 'lucide-react';

const JLPT_LEVELS: (JLPTLevel | 'ALL')[] = ['ALL', 'N5', 'N4', 'N3', 'N2', 'N1'];

export default function MaterialsPage() {
  const [materials, setMaterials] = useState<LearningMaterial[]>([]);
  const [userMaterials, setUserMaterials] = useState<UserMaterial[]>([]);
  const [selectedLevel, setSelectedLevel] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [materialsRes, userMaterialsRes] = await Promise.allSettled([
        materialsApi.getMaterials(selectedLevel !== 'ALL' ? { level: selectedLevel } : undefined),
        userMaterialsApi.getMyMaterials(),
      ]);

      if (materialsRes.status === 'fulfilled') {
        setMaterials(materialsRes.value);
      } else {
        console.warn('Failed to load materials:', materialsRes.reason);
      }

      if (userMaterialsRes.status === 'fulfilled') {
        setUserMaterials(userMaterialsRes.value);
      }
    } catch (err: unknown) {
      console.error('Failed to load materials data:', err);
      setErrorMessage('Không thể tải danh sách tài liệu học tập.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedLevel]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Find map of userMaterials by material id
  const userMaterialMap = new Map<string, UserMaterial>();
  userMaterials.forEach((um) => {
    userMaterialMap.set(um.material.id, um);
  });

  // Active material for continue section: First material with progress < 100 or recently started
  const activeUserMaterial = userMaterials.find((um) => um.progress < 100) || userMaterials[0];

  return (
    <UserAppShell>
      <div className="space-y-8 max-w-4xl mx-auto">
        {/* Header */}
        <header className="space-y-1">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight">
            Tài liệu học tập
          </h1>
          <p className="text-xs sm:text-sm text-stone-500">
            Học tiếng Nhật chuyên ngành IT từ giáo trình và tài liệu chuẩn.
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
            {/* 1. Active / Continue Material */}
            {activeUserMaterial && (
              <section aria-labelledby="continue-material-heading">
                <MaterialContinueCard userMaterial={activeUserMaterial} />
              </section>
            )}

            {/* 2. Material Library */}
            <section aria-labelledby="material-library-heading" className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <h2
                  id="material-library-heading"
                  className="text-base font-bold text-stone-900 tracking-tight"
                >
                  Kho tài liệu học tập
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

              {materials.length === 0 ? (
                <div className="p-12 text-center bg-white rounded-2xl border border-stone-200 space-y-3">
                  <div className="w-12 h-12 rounded-xl bg-stone-100 text-stone-400 flex items-center justify-center mx-auto">
                    <FolderOpen className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-stone-900">
                      Chưa có tài liệu học tập
                    </h3>
                    <p className="text-xs text-stone-500 mt-1">
                      Hiện chưa có tài liệu nào khả dụng. Vui lòng quay lại sau.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {materials.map((m) => (
                    <MaterialCard
                      key={m.id}
                      material={m}
                      userMaterial={userMaterialMap.get(m.id)}
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
