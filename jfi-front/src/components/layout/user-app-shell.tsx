'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { IslandNavigation } from './island-navigation';
import { Button } from '@/components/ui/button';
import {
  LogIn,
  LogOut,
} from 'lucide-react';

interface UserAppShellProps {
  children: React.ReactNode;
}

export function UserAppShell({ children }: UserAppShellProps) {
  const { user, isAuthenticated, logout } = useAuth();

  const displayName = user?.first_name
    ? `${user.first_name} ${user.last_name || ''}`.trim()
    : user?.username || 'Học viên';
  const initials = displayName.substring(0, 2).toUpperCase();

  return (
    <div className="min-h-screen bg-[#faf9f6] text-stone-900 font-sans selection:bg-indigo-100 selection:text-indigo-900 flex flex-col justify-between antialiased">
      {/* Island Navigation */}
      <IslandNavigation />

      {/* Top Application Bar */}
      <header className="sticky top-0 z-30 bg-[#faf9f6]/80 backdrop-blur-md border-b border-stone-200/60 md:pl-24 transition-all">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3.5 flex items-center justify-between">
          {/* Brand Logo & Title */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-xl bg-stone-900 text-white flex items-center justify-center font-bold text-xs shadow-sm group-hover:bg-indigo-600 transition-colors">
              JFI
            </div>
            <div>
              <span className="font-bold text-sm tracking-tight text-stone-900 block leading-tight">
                Japanese for IT
              </span>
              <span className="text-[11px] text-stone-500 hidden sm:block leading-none">
                Tiếng Nhật chuyên ngành Công nghệ thông tin
              </span>
            </div>
          </Link>

          {/* User Status / Auth Actions */}
          <div className="flex items-center gap-2.5">
            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-2.5 py-1 rounded-xl bg-white border border-stone-200 shadow-sm text-xs">
                  <div className="w-6 h-6 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold text-[11px]">
                    {initials}
                  </div>
                  <span className="font-medium text-stone-700 max-w-[120px] truncate hidden sm:inline">
                    {displayName}
                  </span>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => logout()}
                  title="Đăng xuất"
                  className="text-stone-500 hover:text-stone-900 h-8 px-2"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline text-xs ml-1">Đăng xuất</span>
                </Button>
              </div>
            ) : (
              <Button asChild variant="outline" size="sm" className="h-8 text-xs font-medium">
                <Link href="/login">
                  <LogIn className="w-3.5 h-3.5 mr-1" />
                  <span>Đăng nhập</span>
                </Link>
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-4xl mx-auto px-4 sm:px-6 py-6 md:py-10 md:pl-28 pb-28 md:pb-12">
        {children}
      </main>

      {/* Footer */}
      {/* <footer className="md:pl-24 py-6 border-t border-stone-200/60 text-center text-xs text-stone-400">
        <p>JFI — Japanese for IT &copy; {new Date().getFullYear()}・Mỗi ngày một chút tiếng Nhật chuyên ngành</p>
      </footer> */}
    </div>
  );
}
