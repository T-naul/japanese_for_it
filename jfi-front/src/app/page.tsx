'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { UserAppShell } from '@/components/layout/user-app-shell';
import { GuestHome } from '@/components/home/guest-home';
import { OnboardingStudyPlan } from '@/components/home/onboarding-study-plan';
import { TodayStudyCard } from '@/components/home/today-study-card';
import { NextActions } from '@/components/home/next-actions';
import { TodaySummary } from '@/components/home/today-summary';
import { HomeLoading } from '@/components/home/home-loading';
import { HomeErrorState } from '@/components/home/home-empty-state';
import {
  learningApi,
  reviewApi,
  userShadowingApi,
  userMaterialsApi,
} from '@/lib/api';
import { TodayStudyState, ReviewAvailableSummary } from '@/types';

export default function HomePage() {
  const { user, isAuthenticated, isLoading: isAuthLoading } = useAuth();

  const [studyState, setStudyState] = useState<TodayStudyState>({
    hasActivePlan: false,
    isToday: false,
  });
  const [reviewSummary, setReviewSummary] = useState<ReviewAvailableSummary | null>(null);
  const [shadowingCount, setShadowingCount] = useState<number>(0);
  const [materialsCount, setMaterialsCount] = useState<number>(0);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadHomeData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    // If not authenticated, we finish loading immediately to show Guest state
    if (!isAuthenticated) {
      setStudyState({ hasActivePlan: false, isToday: false });
      setReviewSummary(null);
      setShadowingCount(0);
      setMaterialsCount(0);
      setIsLoading(false);
      return;
    }

    try {
      // Parallel fetch from existing backend APIs
      const [todayResult, reviewResult, shadowingResult, materialsResult] =
        await Promise.allSettled([
          learningApi.getTodayStudyState(),
          reviewApi.getAvailableSummary(),
          userShadowingApi.getMyShadowing(),
          userMaterialsApi.getMyMaterials(),
        ]);

      if (todayResult.status === 'fulfilled') {
        setStudyState(todayResult.value);
      } else {
        console.warn('Could not load today study state:', todayResult.reason);
      }

      if (reviewResult.status === 'fulfilled' && reviewResult.value) {
        setReviewSummary(reviewResult.value);
      }

      if (shadowingResult.status === 'fulfilled' && shadowingResult.value) {
        const data = shadowingResult.value;
        const count = Array.isArray(data)
          ? data.length
          : data?.results && Array.isArray(data.results)
            ? data.results.length
            : 0;
        setShadowingCount(count);
      }

      if (materialsResult.status === 'fulfilled' && materialsResult.value) {
        const data = materialsResult.value;
        const count = Array.isArray(data)
          ? data.length
          : data?.results && Array.isArray(data.results)
            ? data.results.length
            : 0;
        setMaterialsCount(count);
      }
    } catch (err: unknown) {
      console.error('Failed to load home page data:', err);
      setErrorMessage('Không thể đồng bộ dữ liệu học tập với máy chủ. Vui lòng thử lại.');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    let ignore = false;
    if (!isAuthLoading) {
      const fetchData = async () => {
        if (!ignore) {
          await loadHomeData();
        }
      };
      void fetchData();
    }
    return () => {
      ignore = true;
    };
  }, [isAuthLoading, loadHomeData]);

  const displayName = user?.first_name || user?.username || user?.email?.split('@')[0] || '';

  return (
    <UserAppShell>
      {/* 1. Loading State */}
      {isAuthLoading || (isAuthenticated && isLoading) ? (
        <HomeLoading />
      ) : !isAuthenticated ? (
        /* 2. Guest / Unauthenticated State */
        <GuestHome />
      ) : errorMessage ? (
        /* 3. API Error State with retry */
        <HomeErrorState message={errorMessage} onRetry={loadHomeData} />
      ) : !studyState.hasActivePlan || !studyState.plan ? (
        /* 4. Authenticated, No Active Study Plan Onboarding */
        <OnboardingStudyPlan displayName={displayName} />
      ) : (
        /* 5. Authenticated + Active Study Plan (Home V2 Main Experience) */
        <div className="space-y-6 max-w-2xl mx-auto sm:mx-0">

          {/* 1. Dominant Today's Study Card */}
          <TodayStudyCard
            studyState={studyState}
            isLoading={isLoading}
          />

          {/* 2. Secondary Next Actions */}
          <NextActions
            reviewSummary={reviewSummary}
            shadowingCount={shadowingCount}
            materialsCount={materialsCount}
          />

          {/* 3. Optional Small Today Summary */}
          {studyState.progress && (
            <TodaySummary
              progress={studyState.progress}
              shadowingCount={shadowingCount}
            />
          )}
        </div>
      )}
    </UserAppShell>
  );
}
