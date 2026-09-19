'use client';

import React, { useEffect, useState } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { contentApi } from '@/lib/api';
import { Vocabulary, Grammar, ContentStatus, STATUS_LABELS } from '@/types';
import {
  BookmarkCheck,
  CheckCircle2,
  Clock,
  BookOpen,
  FileText,
  Sparkles,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

export default function ReviewPage() {
  const [vocabularies, setVocabularies] = useState<Vocabulary[]>([]);
  const [grammars, setGrammars] = useState<Grammar[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [vData, gData] = await Promise.all([
        contentApi.getVocabularies({ page_size: 100 }),
        contentApi.getGrammars({ page_size: 100 }),
      ]);
      setVocabularies(vData.results || []);
      setGrammars(gData.results || []);
    } catch (err) {
      console.error('Error loading review queue:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleApprove = async (type: 'vocabulary' | 'grammar', id: string) => {
    await contentApi.updateItemStatus(type, id, 'accepted');
    await loadData();
  };

  const handleMoveToReview = async (type: 'vocabulary' | 'grammar', id: string) => {
    await contentApi.updateItemStatus(type, id, 'review');
    await loadData();
  };

  // Pending Vocabularies
  const pendingVocabs = vocabularies.filter(
    (v) => v.status === 'upload' || v.status === 'review'
  );

  // Pending Grammars
  const pendingGrammars = grammars.filter(
    (g) => g.status === 'upload' || g.status === 'review'
  );

  const totalPending = pendingVocabs.length + pendingGrammars.length;

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <BookmarkCheck className="w-6 h-6 text-amber-400" />
              Hàng Đợi Duyệt Nội Dung (Review Queue)
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Phê duyệt chất lượng chuyên môn các Từ vựng & Ngữ pháp mới tạo trước khi công khai.
            </p>
          </div>
          <div className="px-4 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm font-bold flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Có {totalPending} mục cần xử lý
          </div>
        </div>

        {totalPending === 0 ? (
          <div className="p-12 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-3">
            <div className="w-16 h-16 rounded-full bg-emerald-500/10 text-emerald-400 mx-auto flex items-center justify-center">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-white">
              Hàng đợi trống! Tất cả nội dung đã được thẩm định.
            </h3>
            <p className="text-slate-400 text-xs max-w-md mx-auto">
              Không có từ vựng hay ngữ pháp nào ở trạng thái Upload hoặc Review.
            </p>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Section 1: Pending Vocabularies */}
            {pendingVocabs.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm font-bold text-indigo-400 uppercase tracking-wider">
                  <BookOpen className="w-4 h-4" />
                  Từ Vựng Chờ Duyệt ({pendingVocabs.length})
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {pendingVocabs.map((vocab) => (
                    <div
                      key={vocab.id}
                      className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between space-y-4"
                    >
                      <div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-extrabold text-white text-lg">
                              {vocab.kanji}
                            </span>
                            <span className="text-xs text-indigo-300 font-mono">
                              ({vocab.hiragana})
                            </span>
                            {vocab.han_viet && (
                              <span className="text-xs text-slate-400">
                                • {vocab.han_viet}
                              </span>
                            )}
                          </div>
                          <span
                            className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
                              STATUS_LABELS[vocab.status].color
                            }`}
                          >
                            {vocab.status}
                          </span>
                        </div>

                        <p className="text-sm text-slate-200 mt-2 font-medium">
                          {vocab.meaning}
                        </p>

                        {vocab.example && (
                          <p className="text-xs text-slate-400 italic mt-2 p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                            Ex: {vocab.example}
                          </p>
                        )}
                      </div>

                      <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                        <span className="text-xs font-bold text-indigo-400">
                          {vocab.level} • {vocab.word_type}
                        </span>

                        <div className="flex items-center gap-2">
                          {vocab.status === 'upload' && (
                            <button
                              onClick={() => handleMoveToReview('vocabulary', vocab.id)}
                              className="px-3 py-1.5 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-xs font-semibold border border-blue-500/20 transition"
                            >
                              Chuyển Review
                            </button>
                          )}
                          <button
                            onClick={() => handleApprove('vocabulary', vocab.id)}
                            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-600/20 transition"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Duyệt Ngay
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Section 2: Pending Grammars */}
            {pendingGrammars.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm font-bold text-violet-400 uppercase tracking-wider">
                  <FileText className="w-4 h-4" />
                  Ngữ Pháp Chờ Duyệt ({pendingGrammars.length})
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {pendingGrammars.map((grammar) => (
                    <div
                      key={grammar.id}
                      className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between space-y-4"
                    >
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="font-extrabold text-violet-300 text-lg">
                            {grammar.pattern}
                          </span>
                          <span
                            className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
                              STATUS_LABELS[grammar.status].color
                            }`}
                          >
                            {grammar.status}
                          </span>
                        </div>

                        <p className="text-sm text-slate-200 mt-2 font-medium">
                          {grammar.meaning}
                        </p>

                        {grammar.example && (
                          <p className="text-xs text-slate-400 italic mt-2 p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                            Ex: {grammar.example}
                          </p>
                        )}
                      </div>

                      <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                        <span className="text-xs font-bold text-violet-400">
                          {grammar.level}
                        </span>

                        <div className="flex items-center gap-2">
                          {grammar.status === 'upload' && (
                            <button
                              onClick={() => handleMoveToReview('grammar', grammar.id)}
                              className="px-3 py-1.5 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-xs font-semibold border border-blue-500/20 transition"
                            >
                              Chuyển Review
                            </button>
                          )}
                          <button
                            onClick={() => handleApprove('grammar', grammar.id)}
                            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-600/20 transition"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Duyệt Ngay
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
