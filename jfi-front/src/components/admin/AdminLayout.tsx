'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { contentApi } from '@/lib/api';
import {
  LayoutDashboard,
  BookOpen,
  FileText,
  BookmarkCheck,
  FolderKanban,
  Menu,
  X,
  Sparkles,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';

interface AdminLayoutProps {
  children: React.ReactNode;
}

const NAV_ITEMS = [
  {
    label: 'Dashboard Tổng quan',
    href: '/admin',
    icon: LayoutDashboard,
    badge: null,
  },
  {
    label: 'Quản lý Từ vựng',
    href: '/admin/vocabularies',
    icon: BookOpen,
    badge: 'Vocab',
  },
  {
    label: 'Quản lý Ngữ pháp',
    href: '/admin/grammars',
    icon: FileText,
    badge: 'Grammar',
  },
  {
    label: 'Nguồn Tài liệu',
    href: '/admin/sources',
    icon: FolderKanban,
    badge: 'Sources',
  },
  {
    label: 'Duyệt Nội dung',
    href: '/admin/review',
    icon: BookmarkCheck,
    badge: 'Review',
    highlight: true,
  },
];

export default function AdminLayout({ children }: AdminLayoutProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean | null>(null);

  useEffect(() => {
    async function checkStatus() {
      const conn = await contentApi.getBackendConnectionStatus();
      setIsBackendConnected(conn.isConnected);
    }
    checkStatus();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col md:flex-row font-sans selection:bg-indigo-500 selection:text-white">
      {/* Mobile Top Navbar */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
            JFI
          </div>
          <span className="font-semibold text-lg tracking-wide text-white">
            Admin Portal
          </span>
        </div>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
        >
          {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar Navigation */}
      <aside
        className={`fixed md:sticky h-screen inset-y-0 left-0 z-50 w-72 bg-slate-900/95 backdrop-blur-xl border-r border-slate-800/80 flex flex-col justify-between transition-transform duration-300 md:translate-x-0 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        <div>
          {/* Brand Header */}
          <div className="p-6 border-b border-slate-800/80 flex items-center justify-between">
            <Link href="/admin" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-0.5 shadow-xl shadow-indigo-500/20 group-hover:scale-105 transition-transform">
                <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-300">
                  JFI
                </div>
              </div>
              <div>
                <div className="font-bold text-white text-base tracking-tight flex items-center gap-1.5">
                  Japanese for IT
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
                </div>
                <span className="text-xs text-slate-400 font-medium">
                  Content Management System
                </span>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="px-3 py-6 space-y-1">
            <div className="px-3 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Quản trị nội dung
            </div>
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group ${isActive
                    ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-600/25'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                    }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`w-5 h-5 transition-transform group-hover:scale-110 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-indigo-400'
                        }`}
                    />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${item.highlight
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : isActive
                          ? 'bg-white/20 text-white'
                          : 'bg-slate-800 text-slate-400'
                        }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Footer / User Profile & System Status */}
        <div className="p-4 border-t border-slate-800/80 space-y-3">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div
                className={`w-2.5 h-2.5 rounded-full ${isBackendConnected === true
                  ? 'bg-emerald-500 animate-ping'
                  : isBackendConnected === false
                    ? 'bg-amber-500'
                    : 'bg-slate-500'
                  }`}
              />
              <span className="text-xs text-slate-300 font-medium">
                {isBackendConnected === true
                  ? 'Django API: Online'
                  : isBackendConnected === false
                    ? 'Django API: Fallback (Offline)'
                    : 'Kiểm tra backend...'}
              </span>
            </div>
            <span className="text-[10px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
              :7000
            </span>
          </div>

          <div className="flex items-center gap-3 p-2 rounded-xl bg-slate-800/40">
            <div className="w-9 h-9 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-white text-sm ring-2 ring-indigo-500/30">
              AD
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-white truncate">
                Admin Manager
              </div>
              <div className="text-xs text-slate-400 truncate">
                admin@jfi-learning.com
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="hidden md:flex items-center justify-between px-8 py-4 bg-slate-900/60 backdrop-blur-md border-b border-slate-800/80 sticky top-0 z-30">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <span>Admin</span>
            <ChevronRight className="w-4 h-4 text-slate-600" />
            <span className="text-slate-200 font-medium capitalize">
              {pathname === '/admin'
                ? 'Dashboard'
                : pathname.replace('/admin/', '')}
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium">
              <ShieldAlert className="w-3.5 h-3.5 text-indigo-400" />
              Permission: Super Admin (IsAdminUser)
            </div> */}
            <Link
              href="/"
              className="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition"
            >
              Trang chủ User
            </Link>
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
