'use client';

import React from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';

interface OnboardingStudyPlanProps {
  displayName?: string;
}

export function OnboardingStudyPlan({ displayName }: OnboardingStudyPlanProps) {
  const name = displayName?.trim() || 'bạn';

  return (
    <div className="py-4 max-w-xl mx-auto sm:mx-0">
      <Card className="border-stone-200/90 shadow-sm bg-white p-6 sm:p-8 space-y-6 rounded-2xl">
        <div className="space-y-1">
          <p className="text-base sm:text-lg font-medium text-stone-700">
            Xin chào, {name}
          </p>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-stone-900">
            Bạn chưa có lộ trình học.
          </h2>
        </div>

        <div className="space-y-2">
          <p className="text-sm text-stone-600 leading-relaxed">
            Chọn cấp độ JLPT và thời gian học
            <br className="hidden sm:inline" />
            để tạo lộ trình học phù hợp với bạn.
          </p>
          <p className="text-xs text-stone-400">
            Lộ trình học tiếng Nhật chuyên ngành IT theo ngày giúp bạn duy trì thói quen học tập đều đặn.
          </p>
        </div>

        <div className="pt-2">
          <Button asChild size="lg" className="w-full sm:w-auto font-semibold px-6 gap-2">
            <Link href="/study">
              <span>Tạo lộ trình học</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </Button>
        </div>
      </Card>
    </div>
  );
}
