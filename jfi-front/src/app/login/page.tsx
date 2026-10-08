'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/common/ToastContext';
import { Button } from '@/components/ui/button';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  Loader2,
  ChevronLeft,
  GraduationCap,
} from 'lucide-react';

function UserLoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnUrl = searchParams.get('returnUrl') || '/';

  const { user, login, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const { showSuccess, showError } = useToast();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // If already authenticated, redirect to returnUrl or home
  useEffect(() => {
    if (!isAuthLoading && isAuthenticated && user) {
      router.replace(returnUrl);
    }
  }, [isAuthLoading, isAuthenticated, user, returnUrl, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setErrorMessage('Vui lòng nhập địa chỉ email.');
      return;
    }

    if (!password) {
      setErrorMessage('Vui lòng nhập mật khẩu.');
      return;
    }

    setIsSubmitting(true);

    try {
      const loggedUser = await login({ email: trimmedEmail, password });
      showSuccess(
        `Chào mừng trở lại, ${loggedUser.first_name || loggedUser.username || 'bạn'}!`,
        'Đăng nhập thành công'
      );
      router.push(returnUrl);
    } catch (err: any) {
      console.error('Login error:', err);
      let message = 'Đăng nhập thất bại. Vui lòng kiểm tra lại email và mật khẩu.';

      if (err.response?.data) {
        const data = err.response.data;
        if (typeof data.error === 'string') {
          message = data.error;
        } else if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (typeof data.non_field_errors === 'string') {
          message = data.non_field_errors;
        } else if (Array.isArray(data.non_field_errors) && data.non_field_errors[0]) {
          message = data.non_field_errors[0];
        } else if (data.email) {
          message = Array.isArray(data.email) ? data.email[0] : String(data.email);
        } else if (data.password) {
          message = Array.isArray(data.password) ? data.password[0] : String(data.password);
        }
      } else if (err.message && err.message.includes('Network Error')) {
        message = 'Không thể kết nối đến máy chủ Django backend (:7000). Vui lòng thử lại sau.';
      }

      setErrorMessage(message);
      showError(message, 'Đăng nhập thất bại');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#faf9f6] text-stone-900 flex flex-col justify-between selection:bg-indigo-100 selection:text-indigo-900">
      {/* Top Navbar */}
      <header className="px-6 py-4 border-b border-stone-200/70 bg-[#faf9f6]/80 backdrop-blur-md">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-xl bg-stone-900 text-white flex items-center justify-center font-bold text-xs shadow-sm group-hover:bg-indigo-600 transition-colors">
              JFI
            </div>
            <div>
              <span className="font-bold text-sm tracking-tight text-stone-900 block leading-tight">
                Japanese for IT
              </span>
              <span className="text-[11px] text-stone-500 hidden sm:block leading-none">
                ITエンジニアのための日本語
              </span>
            </div>
          </Link>

          <Button asChild variant="ghost" size="sm" className="text-xs text-stone-600 hover:text-stone-900">
            <Link href="/" className="flex items-center gap-1">
              <ChevronLeft className="w-4 h-4" />
              <span>Quay lại Trang chủ</span>
            </Link>
          </Button>
        </div>
      </header>

      {/* Main Login Card */}
      <main className="max-w-md w-full mx-auto px-4 sm:px-6 py-10 flex-1 flex flex-col justify-center">
        <div className="p-7 sm:p-9 rounded-3xl bg-white border border-stone-200/90 shadow-[0_8px_30px_rgba(0,0,0,0.04)] space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3 shadow-2xs">
              <GraduationCap className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-stone-900">
              Đăng Nhập Học Viên
            </h1>
            <p className="text-xs sm:text-sm text-stone-500 leading-relaxed max-w-xs mx-auto">
              Tiếp tục hành trình học tiếng Nhật và luyện nói chuyên ngành IT của bạn.
            </p>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5 animate-in fade-in">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
              <div className="flex-1 font-medium leading-relaxed">
                {errorMessage}
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Field */}
            <div className="space-y-1.5">
              <label
                htmlFor="user-email"
                className="block text-xs font-semibold text-stone-700"
              >
                Địa chỉ Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-stone-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  id="user-email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="learner@example.com"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-stone-50 border border-stone-200 text-stone-900 placeholder-stone-400 text-sm focus:outline-none focus:border-indigo-600 focus:bg-white focus:ring-2 focus:ring-indigo-100 transition"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="user-password"
                  className="block text-xs font-semibold text-stone-700"
                >
                  Mật khẩu
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-stone-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="user-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-stone-50 border border-stone-200 text-stone-900 placeholder-stone-400 text-sm focus:outline-none focus:border-indigo-600 focus:bg-white focus:ring-2 focus:ring-indigo-100 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-stone-400 hover:text-stone-600 transition"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              size="lg"
              disabled={isSubmitting}
              className="w-full font-semibold mt-2 text-sm shadow-sm"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Đang đăng nhập...
                </>
              ) : (
                <>
                  Đăng Nhập
                  <ArrowRight className="w-4 h-4 ml-1.5" />
                </>
              )}
            </Button>
          </form>

        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-4 text-center text-xs text-stone-400">
        JFI — Japanese for IT &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
}

export default function UserLoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#faf9f6] flex flex-col items-center justify-center text-stone-400">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mb-2" />
          <span className="text-xs">Đang tải trang đăng nhập...</span>
        </div>
      }
    >
      <UserLoginForm />
    </Suspense>
  );
}
