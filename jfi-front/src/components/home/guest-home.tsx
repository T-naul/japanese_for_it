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

        {/* Japanese Main Concept */}
        <div className="space-y-2">
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-stone-900">
            日本語を、ITの仕事につなげる。
          </h1>
          <p className="text-xs sm:text-sm text-stone-500 leading-relaxed max-w-xs mx-auto">
            ITエンジニアのための日本語学習。
            <br />
            Học tiếng Nhật chuyên ngành Công nghệ thông tin theo lộ trình chuẩn.
          </p>
        </div>

        {/* Single Primary Action: Login */}
        <div className="pt-2">
          <Button asChild size="lg" className="w-full font-semibold shadow-sm">
            <Link href="/login" className="flex items-center justify-center gap-2">
              <LogIn className="w-4 h-4" />
              <span>ログイン (Đăng nhập)</span>
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
