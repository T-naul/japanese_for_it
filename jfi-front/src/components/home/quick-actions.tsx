'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Video,
  BookmarkCheck,
  BookOpen,
  FileText,
  FolderKanban,
  ArrowUpRight,
} from 'lucide-react';

interface QuickActionsProps {
  reviewCount?: number;
  shadowingCount?: number;
}

export function SecondaryQuickActions({
  reviewCount = 0,
  shadowingCount = 0,
}: QuickActionsProps) {
  return (
    <section className="space-y-3.5 my-8">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold uppercase tracking-wider text-stone-500">
          Mở rộng học tập
        </h3>
        <span className="text-xs text-stone-400">Khám phá các phương pháp luyện tập</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {/* Prominent Action 1: Video Shadowing */}
        <Link href="/video" className="group">
          <Card className="h-full border-stone-200/80 bg-white hover:border-indigo-300 hover:shadow-md transition-all p-5 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                  <Video className="w-5 h-5" />
                </div>
                {shadowingCount > 0 ? (
                  <Badge variant="subtle" className="text-[11px]">
                    {shadowingCount} bài đã ghi danh
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-[11px]">
                    Luyện phát âm
                  </Badge>
                )}
              </div>

              <div>
                <h4 className="font-bold text-base text-stone-900 group-hover:text-indigo-600 transition-colors flex items-center gap-1.5">
                  Video Shadowing
                  <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </h4>
                <p className="text-xs text-stone-500 mt-1 leading-relaxed">
                  Luyện nói phản xạ theo ngữ điệu tự nhiên qua các video hội thoại thực tế trong văn phòng và dự án IT.
                </p>
              </div>
            </div>
          </Card>
        </Link>

        {/* Prominent Action 2: Review (Ôn tập ngắt quãng) */}
        <Link href="/review" className="group">
          <Card className="h-full border-stone-200/80 bg-white hover:border-amber-300 hover:shadow-md transition-all p-5 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                  <BookmarkCheck className="w-5 h-5" />
                </div>
                {reviewCount > 0 ? (
                  <Badge variant="warning" className="text-[11px] font-semibold">
                    {reviewCount} mục cần ôn tập
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-[11px]">
                    SRS Review
                  </Badge>
                )}
              </div>

              <div>
                <h4 className="font-bold text-base text-stone-900 group-hover:text-amber-600 transition-colors flex items-center gap-1.5">
                  Ôn tập ngắt quãng
                  <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </h4>
                <p className="text-xs text-stone-500 mt-1 leading-relaxed">
                  Kiểm tra củng cố kiến thức các từ vựng và ngữ pháp đã học bằng thuật toán ngắt quãng để ghi nhớ dài hạn.
                </p>
              </div>
            </div>
          </Card>
        </Link>
      </div>

      {/* Secondary Compact Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
        {/* Vocabulary */}
        <Link href="/vocab" className="group">
          <div className="p-3.5 rounded-xl border border-stone-200/70 bg-white hover:border-stone-300 hover:shadow-xs transition-all flex items-center gap-3">
            <div className="p-2 rounded-lg bg-stone-100 text-stone-700 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
              <BookOpen className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div className="text-xs font-bold text-stone-900 truncate group-hover:text-indigo-600 transition-colors">
                Từ vựng IT
              </div>
              <div className="text-[11px] text-stone-400 truncate">
                Kanji & thể chia động từ
              </div>
            </div>
          </div>
        </Link>

        {/* Grammar */}
        <Link href="/grammar" className="group">
          <div className="p-3.5 rounded-xl border border-stone-200/70 bg-white hover:border-stone-300 hover:shadow-xs transition-all flex items-center gap-3">
            <div className="p-2 rounded-lg bg-stone-100 text-stone-700 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
              <FileText className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div className="text-xs font-bold text-stone-900 truncate group-hover:text-indigo-600 transition-colors">
                Ngữ pháp IT
              </div>
              <div className="text-[11px] text-stone-400 truncate">
                Mẫu câu dự án phần mềm
              </div>
            </div>
          </div>
        </Link>

        {/* Materials */}
        <Link href="/materials" className="group">
          <div className="p-3.5 rounded-xl border border-stone-200/70 bg-white hover:border-stone-300 hover:shadow-xs transition-all flex items-center gap-3">
            <div className="p-2 rounded-lg bg-stone-100 text-stone-700 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
              <FolderKanban className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div className="text-xs font-bold text-stone-900 truncate group-hover:text-indigo-600 transition-colors">
                Tài liệu & PDF
              </div>
              <div className="text-[11px] text-stone-400 truncate">
                Giáo trình & bài giảng
              </div>
            </div>
          </div>
        </Link>
      </div>
    </section>
  );
}
