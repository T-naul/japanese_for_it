'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { LearningMaterial, UserMaterial } from '@/types';
import { FileText, ArrowRight, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

interface MaterialCardProps {
  material: LearningMaterial;
  userMaterial?: UserMaterial | null;
}

export function MaterialCard({ material, userMaterial }: MaterialCardProps) {
  const isEnrolled = !!userMaterial;
  const isReady = material.status === 'ready';
  const isProcessing = material.status === 'processing' || material.status === 'uploaded';
  const isFailed = material.status === 'failed';

  const progress = userMaterial ? Math.round(userMaterial.progress) : 0;
  const completedLessons = userMaterial?.completed_lessons || 0;
  const totalLessons = userMaterial?.total_lessons || 0;

  return (
    <Card className="border-stone-200/90 bg-white shadow-2xs hover:border-stone-300 transition-all rounded-2xl flex flex-col justify-between overflow-hidden">
      <CardHeader className="p-5 pb-3">
        <div className="flex items-center justify-between gap-2 mb-2">
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

          <div>
            {isReady ? (
              isEnrolled && progress >= 100 ? (
                <Badge variant="success" className="gap-1 text-[11px]">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Đã hoàn thành</span>
                </Badge>
              ) : isEnrolled ? (
                <Badge variant="subtle" className="text-[11px]">
                  Đang học
                </Badge>
              ) : (
                <Badge variant="outline" className="text-[11px] text-stone-500">
                  Chưa học
                </Badge>
              )
            ) : isProcessing ? (
              <Badge variant="secondary" className="gap-1 text-[11px] text-amber-700 bg-amber-50 border-amber-200">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>Đang xử lý</span>
              </Badge>
            ) : (
              <Badge variant="destructive" className="gap-1 text-[11px]">
                <AlertCircle className="w-3 h-3" />
                <span>Không khả dụng</span>
              </Badge>
            )}
          </div>
        </div>

        <h3 className="text-base font-bold text-stone-900 tracking-tight line-clamp-2">
          {material.title}
        </h3>

        {material.description && (
          <p className="text-xs text-stone-500 line-clamp-2 mt-1 leading-relaxed">
            {material.description}
          </p>
        )}
      </CardHeader>

      <CardContent className="px-5 py-2">
        {isEnrolled && totalLessons > 0 ? (
          <div className="space-y-1.5 pt-1">
            <div className="flex items-center justify-between text-xs text-stone-500">
              <span>
                Tiến độ: <strong className="text-stone-800 font-semibold">{completedLessons}</strong> / {totalLessons} bài học
              </span>
              <span className="font-bold text-indigo-600 font-mono">{progress}%</span>
            </div>
            <Progress value={progress} className="h-1.5 rounded-full bg-stone-100" />
          </div>
        ) : material.page_count ? (
          <div className="text-xs text-stone-400 flex items-center gap-1.5 pt-1">
            <FileText className="w-3.5 h-3.5" />
            <span>{material.page_count} trang</span>
          </div>
        ) : null}
      </CardContent>

      <CardFooter className="p-5 pt-3 border-t border-stone-100 bg-stone-50/40">
        {isReady ? (
          <Button
            asChild
            variant={isEnrolled ? 'default' : 'outline'}
            size="sm"
            className="w-full justify-between font-semibold"
          >
            <Link href={`/materials/${material.id}`}>
              <span>{isEnrolled ? 'Tiếp tục học' : 'Bắt đầu học'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </Button>
        ) : isProcessing ? (
          <Button disabled size="sm" variant="ghost" className="w-full text-xs text-stone-400">
            <span>Đang xử lý tài liệu...</span>
          </Button>
        ) : (
          <Button disabled size="sm" variant="ghost" className="w-full text-xs text-stone-400">
            <span>Tải tài liệu thất bại</span>
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
