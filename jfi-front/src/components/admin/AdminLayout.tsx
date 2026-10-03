'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { contentApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/common/ToastContext';
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
  LogOut,
  UserCheck,
  Loader2,
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
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const { showSuccess } = useToast();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean | null>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  // Check backend connection
  useEffect(() => {
    async function checkStatus() {
      const conn = await contentApi.getBackendConnectionStatus();
      setIsBackendConnected(conn.isConnected);
    }
    checkStatus();
  }, []);

  // Redirect to login if unauthenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/admin/login?returnUrl=${encodeURIComponent(pathname)}`);
    }
  }, [isLoading, isAuthenticated, router, pathname]);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      showSuccess('Đã đăng xuất khỏi phiên quản trị an toàn.', 'Đăng xuất thành công');
      router.push('/admin/login');
    } catch {
      router.push('/admin/login');
    } finally {
      setIsLoggingOut(false);
    }
  };

  // Loading Screen
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-100 p-6 selection:bg-indigo-500 selection:text-white">
        <div className="flex flex-col items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-0.5 shadow-2xl shadow-indigo-500/30 animate-pulse">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-300 text-xl">
              JFI
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400 font-medium">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
            Đang xác thực phiên quản trị viên...
          </div>
        </div>
      </div>
    );
  }

  // Unauthenticated Fallback
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-100 p-6">
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 text-center max-w-md w-full space-y-4 shadow-2xl">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white">Yêu Cầu Đăng Nhập</h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            Bạn cần đăng nhập tài khoản Quản trị viên để truy cập trang quản lý này.
          </p>
          <div className="pt-2">
            <Link
              href={`/admin/login?returnUrl=${encodeURIComponent(pathname)}`}
              className="inline-flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition"
            >
              Đến Trang Đăng Nhập
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Unauthorized (Not staff) Guard
  if (user && !user.is_staff) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-100 p-6">
        <div className="p-8 rounded-3xl bg-slate-900 border border-rose-500/30 text-center max-w-md w-full space-y-4 shadow-2xl">
          <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white">Từ Chối Quyền Truy Cập</h2>
          <p className="text-xs text-slate-300 leading-relaxed">
            Tài khoản <strong className="text-white">{user.email}</strong> không có quyền Quản trị viên (<code className="text-rose-400">is_staff=false</code>).
          </p>
          <div className="flex flex-col gap-2 pt-2">
            <button
              onClick={handleLogout}
              className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg transition cursor-pointer"
            >
              Đăng xuất & Đổi tài khoản Admin
            </button>
            <Link
              href="/"
              className="w-full py-2 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition text-center"
            >
              Quay lại Trang chủ
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const displayName = user?.first_name
    ? `${user.first_name} ${user.last_name || ''}`.trim()
    : (user?.username || 'Admin User');
  const userInitials = displayName.substring(0, 2).toUpperCase();

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
        <div className="flex items-center gap-2">
          <button
            onClick={handleLogout}
            title="Đăng xuất"
            className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-rose-400 hover:bg-slate-700 transition"
          >
            <LogOut className="w-5 h-5" />
          </button>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
          >
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Sidebar Navigation */}
      <aside
        className={`fixed md:sticky h-screen inset-y-0 left-0 z-50 w-72 bg-slate-900/95 backdrop-blur-xl border-r border-slate-800/80 flex flex-col justify-between transition-transform duration-300 md:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
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
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                    isActive
                      ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-600/25'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`w-5 h-5 transition-transform group-hover:scale-110 ${
                        isActive ? 'text-white' : 'text-slate-400 group-hover:text-indigo-400'
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        item.highlight
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
                className={`w-2.5 h-2.5 rounded-full ${
                  isBackendConnected === true
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

          {/* Authenticated User Card with Logout */}
          <div className="p-2.5 rounded-2xl bg-slate-800/50 border border-slate-800/80 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center font-bold text-white text-xs shadow-md shrink-0 ring-1 ring-white/10">
                {userInitials}
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-white truncate flex items-center gap-1">
                  {displayName}
                  <UserCheck className="w-3 h-3 text-emerald-400 shrink-0" />
                </div>
                <div className="text-[11px] text-slate-400 truncate">
                  {user?.email}
                </div>
              </div>
            </div>

            <button
              onClick={handleLogout}
              disabled={isLoggingOut}
              title="Đăng xuất khỏi Admin"
              className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition shrink-0 cursor-pointer disabled:opacity-50"
            >
              <LogOut className="w-4 h-4" />
            </button>
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

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Admin: {user?.username}</span>
            </div>

            <Link
              href="/"
              className="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition"
            >
              Trang chủ User
            </Link>

            <button
              onClick={handleLogout}
              disabled={isLoggingOut}
              className="flex items-center gap-1.5 text-xs text-rose-300 hover:text-rose-200 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 transition cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Đăng xuất</span>
            </button>
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

