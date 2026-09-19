'use client';

import React, { useEffect, useState } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { contentApi } from '@/lib/api';
import {
  Grammar,
  Source,
  JLPTLevel,
  ContentStatus,
  STATUS_LABELS,
} from '@/types';
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  X,
  FileText,
  BookmarkCheck,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

export default function GrammarsPage() {
  const [grammars, setGrammars] = useState<Grammar[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);

  // Pagination & Filters
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalItems, setTotalItems] = useState(0);

  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Modal States
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<Grammar | null>(null);

  // Form Fields
  const [pattern, setPattern] = useState('');
  const [meaning, setMeaning] = useState('');
  const [level, setLevel] = useState<JLPTLevel>('N3');
  const [example, setExample] = useState('');
  const [status, setStatus] = useState<ContentStatus>('upload');
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [formError, setFormError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [gData, sData] = await Promise.all([
        contentApi.getGrammars({
          page,
          page_size: pageSize,
          search,
          level: levelFilter,
          status: statusFilter,
        }),
        contentApi.getSources(),
      ]);
      setGrammars(gData.results);
      setTotalItems(gData.count);
      setSources(sData.results || []);
    } catch (err) {
      console.error('Error loading grammars:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [page, pageSize, search, levelFilter, statusFilter]);

  const openCreateModal = () => {
    setEditingItem(null);
    setPattern('');
    setMeaning('');
    setLevel('N3');
    setExample('');
    setStatus('upload');
    setSelectedSources([]);
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = async (item: Grammar) => {
    setEditingItem(item);
    setFormError(null);

    try {
      const detail = await contentApi.getGrammarById(item.id);
      setPattern(detail.pattern);
      setMeaning(detail.meaning);
      setLevel(detail.level);
      setExample(detail.example || '');
      setStatus(detail.status);
      setSelectedSources(detail.sources || []);
    } catch (err) {
      setPattern(item.pattern);
      setMeaning(item.meaning);
      setLevel(item.level);
      setExample(item.example || '');
      setStatus(item.status);
      setSelectedSources(item.sources || []);
    }

    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!pattern || !meaning) {
      setFormError('Vui lòng nhập Mẫu ngữ pháp và Ý nghĩa.');
      return;
    }

    try {
      if (editingItem) {
        await contentApi.updateGrammar(editingItem.id, {
          pattern,
          meaning,
          level,
          example,
          status,
          sources: selectedSources,
        });
      } else {
        await contentApi.createGrammar({
          pattern,
          meaning,
          level,
          example,
          status,
          sources: selectedSources,
        });
      }
      setIsModalOpen(false);
      await loadData();
    } catch (err: any) {
      setFormError(err.message || 'Đã xảy ra lỗi khi lưu ngữ pháp.');
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Bạn có chắc muốn xóa mẫu ngữ pháp này?')) {
      await contentApi.deleteGrammar(id);
      await loadData();
    }
  };

  // Pagination Math
  const totalPages = Math.ceil(totalItems / pageSize) || 1;
  const startItem = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, totalItems);

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <FileText className="w-6 h-6 text-violet-400" />
              Quản Lý Ngữ Pháp
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Quản lý các cấu trúc mẫu câu ngữ pháp Tiếng Nhật.
            </p>
          </div>
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-semibold text-sm shadow-lg shadow-violet-600/30 transition hover:-translate-y-0.5"
          >
            <Plus className="w-4 h-4" />
            Thêm Ngữ Pháp Mới
          </button>
        </div>

        {/* Search & Filters Bar */}
        <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3 md:space-y-0 md:flex md:items-center md:gap-4">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Tìm kiếm mẫu ngữ pháp hoặc ý nghĩa..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm placeholder-slate-500 focus:outline-none focus:border-violet-500"
            />
          </div>

          <div className="flex items-center gap-3">
            <select
              value={levelFilter}
              onChange={(e) => {
                setLevelFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 text-sm focus:outline-none focus:border-violet-500"
            >
              <option value="ALL">Tất cả Level</option>
              <option value="N5">Level N5</option>
              <option value="N4">Level N4</option>
              <option value="N3">Level N3</option>
              <option value="N2">Level N2</option>
              <option value="N1">Level N1</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 text-sm focus:outline-none focus:border-violet-500"
            >
              <option value="ALL">Tất cả Trạng thái</option>
              <option value="upload">Upload</option>
              <option value="review">Review</option>
              <option value="accepted">Accepted</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/80 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-6 py-4 whitespace-nowrap">Mẫu Ngữ Pháp</th>
                  <th className="px-6 py-4 whitespace-nowrap">Ý Nghĩa & Ví Dụ IT</th>
                  <th className="px-6 py-4 whitespace-nowrap">Trình Độ</th>
                  <th className="px-6 py-4 whitespace-nowrap">Trạng Thái</th>
                  <th className="px-6 py-4 whitespace-nowrap">Phiên Bản</th>
                  <th className="px-6 py-4 text-right whitespace-nowrap">Thao Tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                      Đang tải danh sách ngữ pháp...
                    </td>
                  </tr>
                ) : grammars.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                      Không có mẫu ngữ pháp nào phù hợp.
                    </td>
                  </tr>
                ) : (
                  grammars.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/40 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-extrabold text-white text-base text-violet-300">
                          {item.pattern}
                        </div>
                      </td>

                      <td className="px-6 py-4 max-w-md">
                        <div className="font-semibold text-slate-200">{item.meaning}</div>
                        {item.example && (
                          <p className="text-xs text-slate-400 italic mt-1 truncate">
                            Ex: {item.example}
                          </p>
                        )}
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center text-xs font-bold px-2.5 py-1 rounded-md bg-violet-500/10 text-violet-400 border border-violet-500/20 whitespace-nowrap">
                          {item.level}
                        </span>
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full border whitespace-nowrap ${
                            STATUS_LABELS[item.status]?.color || 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {STATUS_LABELS[item.status]?.label || item.status}
                        </span>
                      </td>

                      <td className="px-6 py-4 font-mono text-slate-400 text-xs whitespace-nowrap">
                        v{item.version}
                      </td>

                      <td className="px-6 py-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => openEditModal(item)}
                            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-violet-400 hover:bg-slate-700 transition"
                            title="Chỉnh sửa"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(item.id)}
                            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-rose-400 hover:bg-slate-700 transition"
                            title="Xóa"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls Bar */}
          {totalItems > 0 && (
            <div className="p-4 bg-slate-950/80 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
              <div>
                Hiển thị <span className="font-bold text-slate-200">{startItem}</span> -{' '}
                <span className="font-bold text-slate-200">{endItem}</span> trong tổng số{' '}
                <span className="font-bold text-violet-400">{totalItems}</span> mẫu ngữ pháp
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <span>Hiển thị:</span>
                  <select
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setPage(1);
                    }}
                    className="px-2 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-violet-500"
                  >
                    <option value={10}>10 dòng</option>
                    <option value={20}>20 dòng</option>
                    <option value={50}>50 dòng</option>
                  </select>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                    disabled={page <= 1}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:text-white hover:bg-slate-800 transition flex items-center"
                    title="Trang trước"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="px-2 font-medium text-slate-200">
                    Trang {page} / {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
                    disabled={page >= totalPages}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:text-white hover:bg-slate-800 transition flex items-center"
                    title="Trang sau"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Create/Edit */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto scrollbar-hide">
            <div className="relative w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <h3 className="text-lg font-bold text-white">
                  {editingItem ? 'Chỉnh Sửa Ngữ Pháp' : 'Thêm Ngữ Pháp Mới'}
                </h3>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {formError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                  {formError}
                </div>
              )}

              <form onSubmit={handleSave} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Mẫu Ngữ Pháp (Pattern) *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="VD: ～に沿って"
                    value={pattern}
                    onChange={(e) => setPattern(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-violet-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Ý nghĩa *
                  </label>
                  <textarea
                    required
                    rows={2}
                    placeholder="VD: Tuân theo / Dựa theo tài liệu thiết kế"
                    value={meaning}
                    onChange={(e) => setMeaning(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-violet-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">
                      Trình độ JLPT
                    </label>
                    <select
                      value={level}
                      onChange={(e) => setLevel(e.target.value as JLPTLevel)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-violet-500"
                    >
                      <option value="N5">N5</option>
                      <option value="N4">N4</option>
                      <option value="N3">N3</option>
                      <option value="N2">N2</option>
                      <option value="N1">N1</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">
                      Trạng thái
                    </label>
                    <select
                      value={status}
                      onChange={(e) => setStatus(e.target.value as ContentStatus)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-violet-500"
                    >
                      <option value="upload">Upload</option>
                      <option value="review">Review</option>
                      <option value="accepted">Accepted</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Ví dụ
                  </label>
                  <textarea
                    rows={2}
                    placeholder="VD: 設計書に沿ってコードを作成してください。"
                    value={example}
                    onChange={(e) => setExample(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-violet-500"
                  />
                </div>

                {/* Sources Checkboxes */}
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Nguồn Tài Liệu
                  </label>
                  <div className="grid grid-cols-1 gap-2 max-h-32 overflow-y-auto p-2 rounded-xl bg-slate-950 border border-slate-800">
                    {sources.map((s) => {
                      const checked = selectedSources.includes(s.id);
                      return (
                        <label key={s.id} className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedSources([...selectedSources, s.id]);
                              } else {
                                setSelectedSources(selectedSources.filter((id) => id !== s.id));
                              }
                            }}
                            className="rounded border-slate-700 bg-slate-900 text-violet-600"
                          />
                          <span className="truncate">{s.name}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-sm font-medium hover:bg-slate-700"
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold shadow-lg shadow-violet-600/30"
                  >
                    Lưu Ngữ Pháp
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
