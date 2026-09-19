'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import AdminLayout from '@/components/admin/AdminLayout';
import { contentApi } from '@/lib/api';
import { Vocabulary, Grammar, Source } from '@/types';
import {
  BookOpen,
  FileText,
  FolderKanban,
  BookmarkCheck,
  Plus,
  ArrowUpRight,
  Sparkles,
  Layers,
  Activity,
  CheckCircle2,
  Clock,
  Upload,
} from 'lucide-react';

export default function AdminDashboardPage() {
  const [vocabularies, setVocabularies] = useState<Vocabulary[]>([]);
  const [grammars, setGrammars] = useState<Grammar[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [vData, gData, sData] = await Promise.all([
          contentApi.getVocabularies({ page_size: 100 }),
          contentApi.getGrammars({ page_size: 100 }),
          contentApi.getSources({ page_size: 100 }),
        ]);
        setVocabularies(vData.results || []);
        setGrammars(gData.results || []);
        setSources(sData.results || []);
      } catch (err) {
        console.error('Failed to fetch admin dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalVocab = vocabularies.length;
  const totalGrammar = grammars.length;
  const totalSources = sources.length;

  const pendingVocabReview = vocabularies.filter(
    (v) => v.status === 'upload' || v.status === 'review'
  ).length;
  const pendingGrammarReview = grammars.filter(
    (g) => g.status === 'upload' || g.status === 'review'
  ).length;
  const totalPendingReview = pendingVocabReview + pendingGrammarReview;

  // JLPT Level breakdown
  const jlptLevels = ['N5', 'N4', 'N3', 'N2', 'N1'] as const;
  const vocabByLevel = jlptLevels.map((lvl) => ({
    level: lvl,
    count: vocabularies.filter((v) => v.level === lvl).length,
  }));
  const grammarByLevel = jlptLevels.map((lvl) => ({
    level: lvl,
    count: grammars.filter((g) => g.level === lvl).length,
  }));

  // Status breakdown
  const statusCounts = {
    upload:
      vocabularies.filter((v) => v.status === 'upload').length +
      grammars.filter((g) => g.status === 'upload').length,
    review:
      vocabularies.filter((v) => v.status === 'review').length +
      grammars.filter((g) => g.status === 'review').length,
    accepted:
      vocabularies.filter((v) => v.status === 'accepted').length +
      grammars.filter((g) => g.status === 'accepted').length,
  };

  return (
    <AdminLayout>
      <div className="space-y-8">
        {/* Top Banner */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-900/60 via-purple-900/40 to-slate-900 p-6 md:p-8 border border-indigo-500/20 shadow-2xl">
          <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-semibold mb-3">
                <Sparkles className="w-3.5 h-3.5" />
                Hệ Thống Nội Dung Lõi (Content Domain)
              </div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
                Tổng quan Hệ thống Admin JFI
              </h1>
              <p className="text-slate-300 text-sm mt-1 max-w-2xl leading-relaxed">
                Quản lý kho dữ liệu Từ vựng IT, Cấu trúc Ngữ pháp chuyên ngành và Nguồn tài liệu tham khảo cho nền tảng Japanese for IT.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/admin/vocabularies"
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm shadow-lg shadow-indigo-600/30 transition hover:-translate-y-0.5"
              >
                <Plus className="w-4 h-4" />
                Thêm Từ Vựng
              </Link>
              <Link
                href="/admin/grammars"
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm border border-slate-700 transition hover:-translate-y-0.5"
              >
                <Plus className="w-4 h-4" />
                Thêm Ngữ Pháp
              </Link>
            </div>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Card 1: Total Vocab */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition relative overflow-hidden group">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Từ Vựng IT
              </span>
              <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 group-hover:scale-110 transition-transform">
                <BookOpen className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-3">
              <span className="text-3xl font-extrabold text-white">
                {loading ? '...' : totalVocab}
              </span>
              <span className="text-xs text-indigo-400 font-medium">
                từ đã lưu
              </span>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-400">Chờ duyệt: {pendingVocabReview}</span>
              <Link
                href="/admin/vocabularies"
                className="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
              >
                Chi tiết <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>
          </div>

          {/* Card 2: Total Grammar */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition relative overflow-hidden group">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Ngữ Pháp IT
              </span>
              <div className="p-2.5 rounded-xl bg-violet-500/10 text-violet-400 group-hover:scale-110 transition-transform">
                <FileText className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-3">
              <span className="text-3xl font-extrabold text-white">
                {loading ? '...' : totalGrammar}
              </span>
              <span className="text-xs text-violet-400 font-medium">
                mẫu câu
              </span>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-400">Chờ duyệt: {pendingGrammarReview}</span>
              <Link
                href="/admin/grammars"
                className="text-violet-400 hover:text-violet-300 font-medium flex items-center gap-1"
              >
                Chi tiết <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>
          </div>

          {/* Card 3: Total Sources */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition relative overflow-hidden group">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Nguồn Tài Liệu
              </span>
              <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 group-hover:scale-110 transition-transform">
                <FolderKanban className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-3">
              <span className="text-3xl font-extrabold text-white">
                {loading ? '...' : totalSources}
              </span>
              <span className="text-xs text-cyan-400 font-medium">
                tài liệu đính kèm
              </span>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-400">Nguồn tham khảo gốc</span>
              <Link
                href="/admin/sources"
                className="text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
              >
                Quản lý <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>
          </div>

          {/* Card 4: Review Queue */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-amber-500/10 via-slate-900 to-slate-900 border border-amber-500/30 hover:border-amber-500/50 transition relative overflow-hidden group">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
                Hàng Đợi Duyệt
              </span>
              <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-400 group-hover:scale-110 transition-transform">
                <BookmarkCheck className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-3">
              <span className="text-3xl font-extrabold text-amber-400">
                {loading ? '...' : totalPendingReview}
              </span>
              <span className="text-xs text-amber-300 font-medium">
                mục cần duyệt
              </span>
            </div>
            <div className="mt-4 pt-3 border-t border-amber-500/20 flex items-center justify-between text-xs">
              <span className="text-slate-400">Status: Upload / Review</span>
              <Link
                href="/admin/review"
                className="text-amber-400 hover:text-amber-300 font-medium flex items-center gap-1"
              >
                Duyệt ngay <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>
          </div>
        </div>

        {/* Section 2: Distribution & Status Workflow */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Status Breakdown Panel */}
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                Trạng Thái Nội Dung (Content Status)
              </h3>
              <span className="text-xs text-slate-400">Status Workflow</span>
            </div>

            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-slate-950/80 border border-amber-500/20 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                    <Upload className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">
                      Upload (Mới Tạo)
                    </div>
                    <div className="text-xs text-slate-400">
                      Nội dung mới tạo cần rà soát
                    </div>
                  </div>
                </div>
                <span className="text-xl font-bold text-amber-400">
                  {statusCounts.upload}
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/80 border border-blue-500/20 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                    <Clock className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">
                      Review (Đang Thẩm Định)
                    </div>
                    <div className="text-xs text-slate-400">
                      Đang kiểm tra chất lượng chuyên môn
                    </div>
                  </div>
                </div>
                <span className="text-xl font-bold text-blue-400">
                  {statusCounts.review}
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/80 border border-emerald-500/20 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">
                      Accepted
                    </div>
                    <div className="text-xs text-slate-400">
                      Đã xuất bản cho học viên
                    </div>
                  </div>
                </div>
                <span className="text-xl font-bold text-emerald-400">
                  {statusCounts.accepted}
                </span>
              </div>
            </div>
          </div>

          {/* JLPT Level Distribution Chart */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-violet-400" />
                Phân Bổ Theo Trình Độ JLPT (N5 - N1)
              </h3>
              <span className="text-xs text-slate-400">Vocabulary & Grammar</span>
            </div>

            <div className="grid grid-cols-5 gap-3 pt-2">
              {jlptLevels.map((lvl) => {
                const vCount = vocabByLevel.find((b) => b.level === lvl)?.count || 0;
                const gCount = grammarByLevel.find((b) => b.level === lvl)?.count || 0;
                const total = vCount + gCount;
                const maxTotal = Math.max(
                  ...jlptLevels.map(
                    (l) =>
                      (vocabByLevel.find((b) => b.level === l)?.count || 0) +
                      (grammarByLevel.find((b) => b.level === l)?.count || 0)
                  ),
                  1
                );
                const heightPercent = Math.round((total / maxTotal) * 100);

                return (
                  <div key={lvl} className="flex flex-col items-center gap-3">
                    <div className="w-full bg-slate-950 rounded-xl p-2.5 border border-slate-800 flex flex-col items-center justify-end h-44 relative">
                      <div
                        style={{ height: `${Math.max(heightPercent, 10)}%` }}
                        className="w-full rounded-lg bg-gradient-to-t from-indigo-600 via-violet-500 to-purple-400 flex flex-col justify-between p-1.5 transition-all duration-500"
                      >
                        <span className="text-[10px] font-bold text-white text-center">
                          {total}
                        </span>
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs font-bold text-slate-200">{lvl}</div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        {vCount} từ / {gCount} mẫu
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Section 3: Recent Activity / Quick Audit */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white">Dữ Liệu Mới Cập Nhật Trong Hệ Thống</h3>
            <Link
              href="/admin/vocabularies"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              Xem tất cả từ vựng &rarr;
            </Link>
          </div>

          <div className="divide-y divide-slate-800/80 overflow-x-auto">
            {vocabularies.slice(0, 4).map((vocab) => (
              <div key={vocab.id} className="py-3.5 flex items-center justify-between min-w-[500px]">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center font-bold text-indigo-400 text-lg border border-slate-700">
                    {vocab.kanji[0]}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-base">
                        {vocab.kanji}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        ({vocab.hiragana})
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        {vocab.level}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-0.5 truncate max-w-md">
                      {vocab.meaning}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs">
                  <span className="text-slate-400">
                    v{vocab.version}
                  </span>
                  <span
                    className={`font-semibold px-2.5 py-1 rounded-full border ${vocab.status === 'accepted'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        : vocab.status === 'review'
                          ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                          : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                      }`}
                  >
                    {vocab.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
