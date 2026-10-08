'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ReviewAvailableSummary } from '@/types';
import { Video, BookmarkCheck, ArrowRight, CheckCircle2 } from 'lucide-react';

interface NextActionsProps {
  reviewSummary?: ReviewAvailableSummary | null;
  shadowingCount?: number;
  materialsCount?: number;
}

export function NextActions({
  reviewSummary,
}: NextActionsProps) {
  const reviewTotal = reviewSummary?.available ? reviewSummary.total : 0;
  const hasReviews = reviewTotal > 0;

  return (
    <section aria-labelledby="next-actions-heading" className="space-y-3 pt-1">
      <div className="flex items-center justify-between">
        <h3
          id="next-actions-heading"
          className="text-xs font-bold tracking-wider text-stone-600 uppercase"
        >
          次にやること
        </h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {/* 1. Shadowing Card (Actionable - Stronger Visual Priority) */}
        <Card className="border-stone-200/90 bg-white shadow-2xs hover:border-indigo-300 hover:shadow-xs transition-all rounded-xl flex flex-col justify-between">
          <CardHeader className="p-4 sm:p-5 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-base font-bold text-stone-900">
                Shadowing
              </span>
              <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <Video className="w-4 h-4" />
              </div>
            </div>
            <p className="text-xs sm:text-sm text-stone-500 mt-1">
              IT会話を聞いて発音・リズムを練習
            </p>
          </CardHeader>

          <CardFooter className="p-4 sm:p-5 pt-3">
            <Button
              asChild
              size="sm"
              className="w-full justify-between font-semibold shadow-xs"
            >
              <Link href="/video">
                <span>続ける</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </Button>
          </CardFooter>
        </Card>

        {/* 2. Review Card (Contextual: Visually lighter when 0 reviews waiting) */}
        {hasReviews ? (
          /* Actionable Review Card */
          <Card className="border-stone-200/90 bg-white shadow-2xs hover:border-violet-300 hover:shadow-xs transition-all rounded-xl flex flex-col justify-between">
            <CardHeader className="p-4 sm:p-5 pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-base font-bold text-stone-900">
                    Review
                  </span>
                  <Badge variant="subtle" className="text-[10px] font-semibold">
                    {reviewTotal}問
                  </Badge>
                </div>
                <div className="w-8 h-8 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center">
                  <BookmarkCheck className="w-4 h-4" />
                </div>
              </div>
              <p className="text-xs sm:text-sm text-stone-500 mt-1">
                {reviewTotal}問の復習が待っています
              </p>
            </CardHeader>

            <CardFooter className="p-4 sm:p-5 pt-3">
              <Button
                asChild
                variant="outline"
                size="sm"
                className="w-full justify-between font-semibold border-violet-200 text-violet-700 hover:bg-violet-50"
              >
                <Link href="/review">
                  <span>復習する</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </Button>
            </CardFooter>
          </Card>
        ) : (
          /* Unavailable / Muted Review Card (Visually lighter, non-dominant) */
          <Card className="border-stone-200/70 bg-stone-50/50 border-dashed rounded-xl flex flex-col justify-between">
            <CardHeader className="p-4 sm:p-5 pb-2">
              <div className="flex items-center justify-between">
                <span className="text-base font-semibold text-stone-500">
                  Review
                </span>
                <div className="w-8 h-8 rounded-lg bg-stone-100 text-stone-400 flex items-center justify-center">
                  <CheckCircle2 className="w-4 h-4 text-stone-400" />
                </div>
              </div>
              <p className="text-xs sm:text-sm text-stone-400 mt-1">
                待機中の復習はありません
              </p>
            </CardHeader>

            <CardFooter className="p-4 sm:p-5 pt-3">
              <Button
                asChild
                variant="ghost"
                size="sm"
                className="w-full justify-between font-normal text-xs text-stone-400 hover:text-stone-600 hover:bg-stone-100/60"
              >
                <Link href="/review">
                  <span>復習履歴を確認</span>
                  <ArrowRight className="w-3.5 h-3.5 text-stone-300" />
                </Link>
              </Button>
            </CardFooter>
          </Card>
        )}
      </div>
    </section>
  );
}
