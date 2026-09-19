import Link from 'next/link';
import {
  BookOpen,
  FileText,
  FolderKanban,
  BookmarkCheck,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  GraduationCap,
} from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white flex flex-col justify-between">
      {/* Header Bar */}
      <header className="px-6 py-4 border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-0.5 shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-300 text-lg">
                JFI
              </div>
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-tight text-white block">
                Japanese for IT
              </span>
              <span className="text-xs text-slate-400">
                Nền tảng Học Tiếng Nhật Chuyên Ngành IT
              </span>
            </div>
          </div>

          <Link
            href="/admin"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition hover:-translate-y-0.5"
          >
            <ShieldAlert className="w-4 h-4" />
            Truy Cập Admin Portal
          </Link>
        </div>
      </header>

      {/* Main Hero */}
      <main className="max-w-7xl mx-auto px-6 py-16 flex-1 flex flex-col justify-center">
        <div className="text-center space-y-6 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold">
            <Sparkles className="w-4 h-4 text-indigo-400 animate-pulse" />
            Quản Lý Nội Dung Lõi (Backend App Content API Integration)
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight">
            Hệ Thống Admin Quản Lý{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">
              Từ Vựng & Ngữ Pháp IT
            </span>
          </h1>

          <p className="text-slate-300 text-base sm:text-lg leading-relaxed">
            Giao diện Admin Dashboard hoàn chỉnh cho ứng dụng <strong className="text-white">JFI (Japanese for IT)</strong>. Quản lý linh hoạt danh sách từ vựng, thể chia động từ, mẫu câu ngữ pháp và nguồn tài liệu tham khảo.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              href="/admin"
              className="flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-base shadow-xl shadow-indigo-600/30 transition hover:-translate-y-0.5"
            >
              Vào Trang Dashboard Admin
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/admin/review"
              className="flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 font-semibold text-base transition hover:-translate-y-0.5"
            >
              <BookmarkCheck className="w-5 h-5 text-amber-400" />
              Duyệt Bài Mới (Review Queue)
            </Link>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-16">
          <Link
            href="/admin/vocabularies"
            className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 transition group"
          >
            <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 w-fit mb-4 group-hover:scale-110 transition-transform">
              <BookOpen className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white group-hover:text-indigo-400 transition">
              Quản Lý Từ Vựng
            </h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Quản lý Kanji, Hiragana, Hán Việt, Ý nghĩa và bộ công cụ chia thể động từ linh hoạt (`forms`).
            </p>
          </Link>

          <Link
            href="/admin/grammars"
            className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-violet-500/50 transition group"
          >
            <div className="p-3 rounded-xl bg-violet-500/10 text-violet-400 w-fit mb-4 group-hover:scale-110 transition-transform">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white group-hover:text-violet-400 transition">
              Quản Lý Ngữ Pháp
            </h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Lưu trữ các cấu trúc ngữ pháp mẫu câu, ví dụ thực tế trong dự án IT và phân cấp trình độ JLPT.
            </p>
          </Link>

          <Link
            href="/admin/sources"
            className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/50 transition group"
          >
            <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400 w-fit mb-4 group-hover:scale-110 transition-transform">
              <FolderKanban className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white group-hover:text-cyan-400 transition">
              Nguồn Tài Liệu Tham Khảo
            </h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Quản lý danh sách sách, tài liệu gốc, giáo trình và liên kết Many-to-Many với Từ vựng & Ngữ pháp.
            </p>
          </Link>

          <Link
            href="/admin/review"
            className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/50 transition group"
          >
            <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 w-fit mb-4 group-hover:scale-110 transition-transform">
              <BookmarkCheck className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white group-hover:text-amber-400 transition">
              Duyệt Bài Tập Trung
            </h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Thẩm định nội dung mới tạo (chuyển trạng thái từ `upload` / `review` sang `accepted`).
            </p>
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-6 border-t border-slate-800/80 text-center text-xs text-slate-500">
        JFI (Japanese for IT) - Platform Admin Portal Built with Next.js & Tailwind CSS
      </footer>
    </div>
  );
}
