'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { LogIn } from 'lucide-react';

export function GuestHome() {
  return (
    <div className="flex flex-col items-center justify-center py-12 sm:py-20">
      <Card className="max-w-md w-full p-8 sm:p-10 border-stone-200/90 shadow-sm bg-white text-center space-y-6 rounded-3xl">
        {/* Brand Glyph */}
        <div className="w-14 h-14 rounded-2xl bg-stone-900 text-white flex items-center justify-center font-extrabold text-base shadow-sm mx-auto">
          JFI
        </div>

        {/* Main concept */}
        <div className="space-y-2">
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-stone-900">
            Kết nối tiếng Nhật với công việc IT.
          </h1>
          <p className="text-xs sm:text-sm text-stone-500 leading-relaxed max-w-xs mx-auto">
            Học tiếng Nhật dành cho kỹ sư Công nghệ thông tin.
            <br />
            Học theo lộ trình bài bản, gắn với công việc thực tế.
          </p>
        </div>

        {/* Single Primary Action: Login */}
        <div className="pt-2">
          <Button asChild size="lg" className="w-full font-semibold shadow-sm">
            <Link href="/login" className="flex items-center justify-center gap-2">
              <LogIn className="w-4 h-4" />
              <span>Đăng nhập</span>
            </Link>
          </Button>
        </div>

        <p className="text-[11px] text-stone-400">
          Đăng nhập để theo dõi bài học mỗi ngày và đồng bộ tiến độ học tập của bạn.
        </p>
      </Card>
    </div>
  );
}
