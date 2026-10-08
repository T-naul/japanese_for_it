'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  Home,
  Video,
  BookOpenCheck,
  MoreHorizontal,
  BookmarkCheck,
  FolderKanban,
  BookOpen,
  FileText,
  BarChart3,
  Settings,
  User,
  X,
} from 'lucide-react';
import { createPortal } from "react-dom";

interface NavItem {
  label: string;
  jpLabel: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const PRIMARY_NAV_ITEMS: NavItem[] = [
  {
    label: 'Home',
    jpLabel: 'ホーム',
    href: '/',
    icon: Home,
  },

  {
    label: 'Study',
    jpLabel: '学習',
    href: '/study',
    icon: BookOpenCheck,
  },
  {
    label: 'Video',
    jpLabel: '動画 (Shadowing)',
    href: '/video',
    icon: Video,
  },
];

const MORE_NAV_ITEMS = [
  {
    label: 'Ôn tập kiến thức',
    jpLabel: '復習 (Review)',
    description: 'Củng cố từ vựng & ngữ pháp IT đã học',
    href: '/review',
    icon: BookmarkCheck,
  },
  {
    label: 'Tài liệu học tập',
    jpLabel: '教材 (Materials)',
    description: 'Giáo trình và bài học chuyên sâu',
    href: '/materials',
    icon: FolderKanban,
  },
  {
    label: 'Kho Từ vựng',
    jpLabel: '単語 (Vocabulary)',
    description: 'Tra cứu Kanji, thể chia động từ',
    href: '/vocab',
    icon: BookOpen,
  },
  {
    label: 'Kho Ngữ pháp',
    jpLabel: '文法 (Grammar)',
    description: 'Mẫu câu thực tế trong dự án IT',
    href: '/grammar',
    icon: FileText,
  },
  {
    label: 'Tiến độ học tập',
    jpLabel: '進捗 (Progress)',
    description: 'Thống kê tỷ lệ hoàn thành',
    href: '/progress',
    icon: BarChart3,
  },
  {
    label: 'Cài đặt',
    jpLabel: '設定 (Settings)',
    description: 'Tùy chỉnh thông báo và giao diện',
    href: '/settings',
    icon: Settings,
  },
  {
    label: 'Hồ sơ cá nhân',
    jpLabel: 'プロフィール (Profile)',
    description: 'Thông tin tài khoản học viên',
    href: '/profile',
    icon: User,
  },
];

export function IslandNavigation() {
  const pathname = usePathname();
  const [showMoreMenu, setShowMoreMenu] = useState(false);

  return (
    <>
      {/* Desktop: Floating Vertical Island Navigation on Left */}
      <aside
        aria-label="Điều hướng chính"
        className="fixed left-6 top-1/2 -translate-y-1/2 z-40 hidden md:flex flex-col items-center gap-1.5 p-2 rounded-2xl bg-white/95 backdrop-blur-md border border-stone-200/90 shadow-[0_8px_30px_rgba(0,0,0,0.06)]"
      >
        {/* Primary Items */}
        {PRIMARY_NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.label}
              className={cn(
                'group relative flex flex-col items-center justify-center w-12 h-12 rounded-xl transition-all',
                isActive
                  ? 'bg-indigo-50 text-indigo-600 font-semibold shadow-inner'
                  : 'text-stone-500 hover:text-stone-900 hover:bg-stone-100/80'
              )}
            >
              <Icon className="w-5 h-5 transition-transform group-hover:scale-110" />
              <span className="text-[10px] mt-0.5 tracking-tight font-medium">
                {item.label}
              </span>

              {/* Tooltip on hover */}
              <div className="pointer-events-none absolute left-full ml-3 hidden group-hover:flex items-center px-2.5 py-1 rounded-lg bg-stone-900 text-white text-xs whitespace-nowrap shadow-md z-50">
                <span>{item.jpLabel}</span>
              </div>
            </Link>
          );
        })}

        {/* More Trigger */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowMoreMenu(!showMoreMenu)}
            aria-label="Thêm mục học tập"
            aria-expanded={showMoreMenu}
            className={cn(
              'group relative flex flex-col items-center justify-center w-12 h-12 rounded-xl transition-all cursor-pointer',
              showMoreMenu
                ? 'bg-stone-200/80 text-stone-900'
                : 'text-stone-500 hover:text-stone-900 hover:bg-stone-100/80'
            )}
          >
            <MoreHorizontal className="w-5 h-5 transition-transform group-hover:scale-110" />
            <span className="text-[10px] mt-0.5 tracking-tight font-medium">
              Thêm
            </span>
          </button>

          {/* Desktop More Menu Flyout */}
          {showMoreMenu && (
            <>
              {createPortal(
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowMoreMenu(false)}
                />,
                document.body
              )}
              <div className="absolute left-full bottom-0 ml-3 z-50 w-72 p-3 rounded-2xl bg-white border border-stone-200 shadow-xl animate-in fade-in zoom-in-95 duration-150">
                <div className="px-2 py-1.5 mb-1 flex items-center justify-between border-b border-stone-100">
                  <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">
                    Mục học tập khác
                  </span>
                  <button
                    onClick={() => setShowMoreMenu(false)}
                    className="p-1 rounded-md text-stone-400 hover:text-stone-600 hover:bg-stone-100"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="space-y-1">
                  {MORE_NAV_ITEMS.map((subItem) => {
                    const SubIcon = subItem.icon;
                    return (
                      <Link
                        key={subItem.href}
                        href={subItem.href}
                        onClick={() => setShowMoreMenu(false)}
                        className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-stone-50 transition-colors group"
                      >
                        <div className="p-2 rounded-lg bg-stone-100 text-stone-600 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors shrink-0">
                          <SubIcon className="w-4 h-4" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="text-xs font-semibold text-stone-900 flex items-center gap-1.5">
                            {subItem.label}
                            <span className="text-[10px] text-stone-400 font-normal">
                              {subItem.jpLabel}
                            </span>
                          </div>
                          <p className="text-[11px] text-stone-500 truncate mt-0.5">
                            {subItem.description}
                          </p>
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </aside>

      {/* Mobile: Floating Horizontal Island Navigation near Bottom */}
      <nav
        aria-label="Điều hướng di động"
        className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 md:hidden flex items-center justify-around gap-1 px-3 py-2 rounded-2xl bg-white/95 backdrop-blur-md border border-stone-200/90 shadow-[0_8px_32px_rgba(0,0,0,0.12)] w-[92%] max-w-sm"
      >
        {PRIMARY_NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-col items-center justify-center flex-1 py-1 px-2 rounded-xl transition-all',
                isActive
                  ? 'text-indigo-600 font-semibold'
                  : 'text-stone-500 hover:text-stone-900 active:bg-stone-100'
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] mt-0.5 font-medium tracking-tight">
                {item.label}
              </span>
            </Link>
          );
        })}

        {/* Mobile More Button */}
        <button
          type="button"
          onClick={() => setShowMoreMenu(!showMoreMenu)}
          aria-label="Xem thêm các mục khác"
          className={cn(
            'flex flex-col items-center justify-center flex-1 py-1 px-2 rounded-xl transition-all cursor-pointer',
            showMoreMenu
              ? 'text-indigo-600 font-semibold'
              : 'text-stone-500 hover:text-stone-900 active:bg-stone-100'
          )}
        >
          <MoreHorizontal className="w-5 h-5" />
          <span className="text-[10px] mt-0.5 font-medium tracking-tight">
            Thêm
          </span>
        </button>
      </nav>

      {/* Mobile More Sheet / Dialog */}
      {showMoreMenu && (
        <div className="fixed inset-0 z-50 md:hidden flex flex-col justify-end">
          <div
            className="fixed inset-0 bg-stone-900/40 backdrop-blur-sm"
            onClick={() => setShowMoreMenu(false)}
          />
          <div className="relative z-10 p-5 rounded-t-3xl bg-white border-t border-stone-200 shadow-2xl max-h-[80vh] overflow-y-auto animate-in slide-in-from-bottom duration-200">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-stone-100">
              <h3 className="text-sm font-semibold text-stone-900">
                Tất cả tính năng học tập
              </h3>
              <button
                onClick={() => setShowMoreMenu(false)}
                className="p-1.5 rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="grid grid-cols-1 gap-2 pb-6">
              {MORE_NAV_ITEMS.map((subItem) => {
                const SubIcon = subItem.icon;
                return (
                  <Link
                    key={subItem.href}
                    href={subItem.href}
                    onClick={() => setShowMoreMenu(false)}
                    className="flex items-center gap-3.5 p-3 rounded-xl hover:bg-stone-50 active:bg-stone-100 transition-colors border border-stone-100"
                  >
                    <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600 shrink-0">
                      <SubIcon className="w-5 h-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-semibold text-stone-900">
                        {subItem.label}
                      </div>
                      <p className="text-xs text-stone-500 truncate">
                        {subItem.description}
                      </p>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
