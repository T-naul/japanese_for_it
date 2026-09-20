'use client';

import React, { useEffect, useState } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { contentApi } from '@/lib/api';
import {
  Vocabulary,
  VocabularyForm,
  Source,
  JLPTLevel,
  ContentStatus,
  WordType,
  VerbFormType,
  VERB_FORM_LABELS,
  WORD_TYPE_LABELS,
  STATUS_LABELS,
} from '@/types';
import FileImportModal from '@/components/admin/FileImportModal';
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  X,
  Layers,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Upload,
} from 'lucide-react';


const ALL_VERB_FORM_TYPES: VerbFormType[] = [
  'suru',
  'masu',
  'nai',
  'ta',
  'te',
  'kano',
  'ukemi',
  'shieki',
  'shieki_ukemi',
  'imperative',
  'ikou',
  'kenshi',
  'jiouken',
];

const DEFAULT_VERB_FORMS_MAP: Record<VerbFormType, string> = {
  suru: '',
  masu: '',
  nai: '',
  ta: '',
  te: '',
  kano: '',
  ukemi: '',
  shieki: '',
  shieki_ukemi: '',
  imperative: '',
  ikou: '',
  kenshi: '',
  jiouken: '',
};

const isVerb = (type: string) =>
  type === 'verb' ||
  type === 'verb_1' ||
  type === 'verb_2' ||
  type === 'verb_3' ||
  type === 'verb-1' ||
  type === 'verb-2' ||
  type === 'verb-3';

export default function VocabulariesPage() {
  const [vocabularies, setVocabularies] = useState<Vocabulary[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);

  // Pagination & Filtering
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalItems, setTotalItems] = useState(0);

  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Modal States
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<Vocabulary | null>(null);
  const [viewingItem, setViewingItem] = useState<Vocabulary | null>(null);


  // Form Fields
  const [kanji, setKanji] = useState('');
  const [hiragana, setHiragana] = useState('');
  const [hanViet, setHanViet] = useState('');
  const [meaning, setMeaning] = useState('');
  const [wordType, setWordType] = useState<WordType>('verb_1');
  const [level, setLevel] = useState<JLPTLevel>('N3');
  const [example, setExample] = useState('');
  const [status, setStatus] = useState<ContentStatus>('upload');
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [verbFormsMap, setVerbFormsMap] = useState<Record<VerbFormType, string>>(DEFAULT_VERB_FORMS_MAP);
  const [formError, setFormError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [vRes, sRes] = await Promise.all([
        contentApi.getVocabularies({
          page,
          page_size: pageSize,
          search: debouncedSearch,
          level: levelFilter,
          word_type: typeFilter,
          status: statusFilter,
        }),
        contentApi.getSources(),
      ]);
      setVocabularies(vRes.results);
      setTotalItems(vRes.count);
      setSources(sRes.results || []);
    } catch (err) {
      console.error('Error loading vocabularies:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 400); // chờ 400ms sau khi ngừng gõ mới gọi API

    return () => clearTimeout(timer); // hủy timer cũ nếu người dùng gõ tiếp
  }, [search]);

  useEffect(() => {
    loadData();
  }, [page, pageSize, debouncedSearch, levelFilter, typeFilter, statusFilter]);

  const openCreateModal = () => {
    setEditingItem(null);
    setKanji('');
    setHiragana('');
    setHanViet('');
    setMeaning('');
    setWordType('verb_1');
    setLevel('N3');
    setExample('');
    setStatus('upload');
    setSelectedSources([]);
    setVerbFormsMap({ ...DEFAULT_VERB_FORMS_MAP });
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = async (item: Vocabulary) => {
    setEditingItem(item);
    setFormError(null);

    try {
      const detail = await contentApi.getVocabularyById(item.id);
      setKanji(detail.kanji);
      setHiragana(detail.hiragana);
      setHanViet(detail.han_viet || '');
      setMeaning(detail.meaning);
      setWordType(detail.word_type);
      setLevel(detail.level);
      setExample(detail.example || '');
      setStatus(detail.status);
      setSelectedSources(detail.sources || []);

      const newMap: Record<VerbFormType, string> = { ...DEFAULT_VERB_FORMS_MAP };
      if (detail.forms) {
        detail.forms.forEach((f) => {
          if (f.form_type) {
            newMap[f.form_type] = f.value;
          }
        });
      }
      setVerbFormsMap(newMap);
    } catch (err) {
      setKanji(item.kanji);
      setHiragana(item.hiragana);
      setHanViet(item.han_viet || '');
      setMeaning(item.meaning);
      setWordType(item.word_type);
      setLevel(item.level);
      setExample(item.example || '');
      setStatus(item.status);
      setSelectedSources(item.sources || []);

      const newMap: Record<VerbFormType, string> = { ...DEFAULT_VERB_FORMS_MAP };
      if (item.forms) {
        item.forms.forEach((f) => {
          if (f.form_type) {
            newMap[f.form_type] = f.value;
          }
        });
      }
      setVerbFormsMap(newMap);
    }

    setIsModalOpen(true);
  };

  const handleViewDetail = async (item: Vocabulary) => {
    try {
      const detail = await contentApi.getVocabularyById(item.id);
      setViewingItem(detail);
    } catch (err) {
      setViewingItem(item);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!kanji.trim() || !hiragana.trim() || !meaning.trim()) {
      setFormError('Vui lòng điền đầy đủ Kanji, Hiragana và Ý nghĩa.');
      return;
    }

    let validForms: VocabularyForm[] = [];
    if (isVerb(wordType)) {
      validForms = ALL_VERB_FORM_TYPES
        .filter((typeKey) => verbFormsMap[typeKey] && verbFormsMap[typeKey].trim() !== '')
        .map((typeKey) => ({
          form_type: typeKey,
          value: verbFormsMap[typeKey].trim(),
        }));
    }

    try {
      if (editingItem) {
        await contentApi.updateVocabulary(editingItem.id, {
          kanji,
          hiragana,
          han_viet: hanViet,
          meaning,
          word_type: wordType,
          level,
          example,
          status,
          sources: selectedSources,
          forms: isVerb(wordType) ? validForms : [],
        });
      } else {
        await contentApi.createVocabulary({
          kanji,
          hiragana,
          han_viet: hanViet,
          meaning,
          word_type: wordType,
          level,
          example,
          status,
          sources: selectedSources,
          forms: isVerb(wordType) ? validForms : [],
        });
      }
      setIsModalOpen(false);
      await loadData();
    } catch (err: any) {
      setFormError(err.message || 'Đã xảy ra lỗi khi lưu từ vựng.');
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Bạn có chắc chắn muốn xóa từ vựng này?')) {
      await contentApi.deleteVocabulary(id);
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
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <Layers className="w-6 h-6 text-indigo-400" />
              Quản Lý Từ Vựng
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Quản lý danh sách từ vựng tiếng Nhật, chia thể động từ và từ đồng nghĩa.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-300 font-semibold text-sm border border-slate-700 shadow-md transition hover:-translate-y-0.5"
            >
              <Upload className="w-4 h-4" />
              Import Từ File
            </button>
            <button
              onClick={openCreateModal}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition hover:-translate-y-0.5"
            >
              <Plus className="w-4 h-4" />
              Thêm Từ Vựng Mới
            </button>
          </div>
        </div>


        {/* Search & Filters Bar */}
        <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3 md:space-y-0 md:flex md:items-center md:gap-4">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Tìm kiếm ..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Filter Dropdowns */}
          <div className="flex flex-wrap items-center gap-3">
            <select
              value={levelFilter}
              onChange={(e) => {
                setLevelFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">Tất cả Trình độ (JLPT)</option>
              <option value="N5">Level N5</option>
              <option value="N4">Level N4</option>
              <option value="N3">Level N3</option>
              <option value="N2">Level N2</option>
              <option value="N1">Level N1</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">Tất cả Loại từ</option>
              <option value="noun">Danh từ</option>
              <option value="verb_1">Động từ nhóm 1</option>
              <option value="verb_2">Động từ nhóm 2</option>
              <option value="verb_3">Động từ nhóm 3</option>
              <option value="adjective">Tính từ</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">Tất cả Trạng thái</option>
              <option value="upload">Upload</option>
              <option value="review">Review</option>
              <option value="accepted">Accepted</option>
            </select>
          </div>
        </div>

        {/* Vocabularies Table */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/80 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-6 py-4 whitespace-nowrap">Từ Vựng & Hán Việt</th>
                  <th className="px-6 py-4 whitespace-nowrap">Ý Nghĩa</th>
                  <th className="px-6 py-4 whitespace-nowrap">Loại Từ</th>
                  <th className="px-6 py-4 whitespace-nowrap">Trình Độ</th>
                  <th className="px-6 py-4 whitespace-nowrap">Trạng Thái</th>
                  <th className="px-6 py-4 text-right whitespace-nowrap">Thao Tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                      Đang tải danh sách từ vựng...
                    </td>
                  </tr>
                ) : vocabularies.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                      Không tìm thấy từ vựng nào khớp với bộ lọc.
                    </td>
                  </tr>
                ) : (
                  vocabularies.map((item) => (
                    <tr
                      key={item.id}
                      className="hover:bg-slate-800/40 transition group"
                    >
                      <td
                        className="px-6 py-4 whitespace-nowrap cursor-pointer hover:text-indigo-300"
                        onClick={() => handleViewDetail(item)}
                      >
                        <div className="flex items-center gap-3">
                          <div>
                            <div className="font-bold text-white text-base">
                              {item.kanji}
                            </div>
                            <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                              <span className="text-indigo-300 font-mono">
                                {item.hiragana}
                              </span>
                              {item.han_viet && (
                                <span className="text-slate-500">
                                  • {item.han_viet}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4 max-w-xs truncate text-slate-200">
                        {item.meaning}
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center text-xs px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700 whitespace-nowrap">
                          {WORD_TYPE_LABELS[item.word_type] || item.word_type}
                        </span>
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center text-xs font-bold px-2.5 py-1 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 whitespace-nowrap">
                          {item.level}
                        </span>
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full border whitespace-nowrap ${STATUS_LABELS[item.status]?.color || 'bg-slate-800 text-slate-300'
                            }`}
                        >
                          {STATUS_LABELS[item.status]?.label || item.status}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => openEditModal(item)}
                            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-indigo-400 hover:bg-slate-700 transition"
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
                <span className="font-bold text-indigo-400">{totalItems}</span> từ vựng
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
                    className="px-2 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
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

        {/* Modal Create/Edit Vocabulary */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
            <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6 my-8">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <h3 className="text-lg font-bold text-white">
                  {editingItem ? 'Chỉnh Sửa Từ Vựng' : 'Thêm Từ Vựng Mới'}
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
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">
                      Kanji *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="VD: 実装する"
                      value={kanji}
                      onChange={(e) => setKanji(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">
                      Hiragana *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="VD: じっそうする"
                      value={hiragana}
                      onChange={(e) => setHiragana(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">
                      Hán Việt
                    </label>
                    <input
                      type="text"
                      placeholder="VD: Thực trang"
                      value={hanViet}
                      onChange={(e) => setHanViet(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Ý nghĩa *
                  </label>
                  <textarea
                    required
                    rows={2}
                    placeholder="VD: Lập trình cài đặt chức năng hệ thống"
                    value={meaning}
                    onChange={(e) => setMeaning(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">
                      Loại từ
                    </label>
                    <select
                      value={wordType}
                      onChange={(e) => setWordType(e.target.value as WordType)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                    >
                      <option value="noun">Danh từ</option>
                      <option value="verb_1">Động từ nhóm 1</option>
                      <option value="verb_2">Động từ nhóm 2</option>
                      <option value="verb_3">Động từ nhóm 3</option>
                      <option value="adjective">Tính từ</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">
                      Trình độ JLPT
                    </label>
                    <select
                      value={level}
                      onChange={(e) => setLevel(e.target.value as JLPTLevel)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
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
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
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
                    placeholder="VD: 仕様書に基づいてAPIを実装します。"
                    value={example}
                    onChange={(e) => setExample(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>

                {/* Fixed Verb Form Manager (Only when wordType is a Verb group) */}
                {isVerb(wordType) ? (
                  <div className="p-4 rounded-xl bg-slate-950 border border-indigo-500/20 space-y-3">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-indigo-400 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5" />
                        Thể Động Từ
                      </label>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-60 overflow-y-auto pr-1">
                      {ALL_VERB_FORM_TYPES.map((typeKey) => (
                        <div key={typeKey} className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                          <label className="block text-[11px] font-semibold text-slate-300">
                            {VERB_FORM_LABELS[typeKey]}
                          </label>
                          <input
                            type="text"
                            placeholder={`VD: ${typeKey === 'masu'
                              ? '実装します'
                              : typeKey === 'nai'
                                ? '実装しない'
                                : typeKey === 'ta'
                                  ? '実装した'
                                  : typeKey === 'te'
                                    ? '実装して'
                                    : 'Nhập giá trị...'
                              }`}
                            value={verbFormsMap[typeKey] || ''}
                            onChange={(e) =>
                              setVerbFormsMap((prev) => ({
                                ...prev,
                                [typeKey]: e.target.value,
                              }))
                            }
                            className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800 text-xs text-slate-500">
                    * Thể động từ chỉ áp dụng khi Loại từ được chọn thuộc các nhóm <b>Động từ (verb)</b>.
                  </div>
                )}

                {/* Sources Selector */}
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Nguồn Tài Liệu
                  </label>
                  <div className="grid grid-cols-1 gap-2 max-h-32 overflow-y-auto p-2 rounded-xl bg-slate-950 border border-slate-800">
                    {sources.map((s) => {
                      const checked = selectedSources.includes(s.id);
                      return (
                        <label
                          key={s.id}
                          className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedSources([...selectedSources, s.id]);
                              } else {
                                setSelectedSources(
                                  selectedSources.filter((id) => id !== s.id)
                                );
                              }
                            }}
                            className="rounded border-slate-700 bg-slate-900 text-indigo-600"
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
                    className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/30"
                  >
                    Lưu Từ Vựng
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Quick Detail View Drawer/Modal */}
        {viewingItem && (
          <div className="fixed inset-0 z-50 flex justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto scrollbar-hide [align-items:safe_center]">
            <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-5">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center font-extrabold text-2xl">
                    {viewingItem.kanji[0]}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">
                      {viewingItem.kanji}
                    </h3>
                    <div className="text-xs text-indigo-300 font-mono">
                      {viewingItem.hiragana} {viewingItem.han_viet && `• ${viewingItem.han_viet}`}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setViewingItem(null)}
                  className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-xs font-semibold text-slate-400 uppercase">Ý nghĩa:</span>
                  <p className="text-slate-200 font-medium mt-0.5">{viewingItem.meaning}</p>
                </div>

                <div className="flex items-center gap-4 text-xs">
                  <div>
                    <span className="text-slate-400">Loại từ: </span>
                    <span className="font-semibold text-white">
                      {WORD_TYPE_LABELS[viewingItem.word_type] || viewingItem.word_type}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">Trình độ: </span>
                    <span className="font-bold text-indigo-400">{viewingItem.level}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Version: </span>
                    <span className="font-mono text-slate-300">v{viewingItem.version}</span>
                  </div>
                </div>

                {viewingItem.example && (
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-xs font-semibold text-slate-400">Ví dụ</span>
                    <p className="text-xs text-slate-300 italic mt-1">{viewingItem.example}</p>
                  </div>
                )}

                {/* Verb Forms List */}
                {viewingItem.forms && viewingItem.forms.length > 0 && (
                  <div>
                    <span className="text-xs font-semibold text-indigo-400">Các thể chia động từ:</span>
                    <div className="grid grid-cols-2 gap-2 mt-1.5">
                      {viewingItem.forms.map((f, i) => (
                        <div key={i} className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-xs">
                          <span className="text-slate-400 block text-[10px]">
                            {VERB_FORM_LABELS[f.form_type] || f.form_type}
                          </span>
                          <span className="font-semibold text-indigo-300">{f.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end">
                <button
                  onClick={() => setViewingItem(null)}
                  className="px-4 py-1.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700"
                >
                  Đóng
                </button>
              </div>
            </div>
          </div>
        )}

        {/* File Import Modal */}
        <FileImportModal
          isOpen={isImportModalOpen}
          onClose={() => setIsImportModalOpen(false)}
          title="Import Từ Vựng Từ File"
          description="Tải lên file định dạng .json, .csv, hoặc .xlsx để thêm từ vựng mới hàng loạt."
          onUpload={(file) => contentApi.importVocabularies(file)}
          onSuccess={() => loadData()}
          sampleInfo={{
            filenamePrefix: 'vocabularies',
            headers: ['kanji', 'hiragana', 'meaning', 'han_viet', 'word_type', 'level', 'status', 'example', 'forms'],
            exampleJson: [
              {
                kanji: '実装する',
                hiragana: 'じっそうする',
                meaning: 'Lập trình cài đặt chức năng hệ thống',
                han_viet: 'Thực trang',
                word_type: 'verb_3',
                level: 'N3',
                status: 'upload',
                example: '仕様書に基づいてAPIを実装します。',
                forms: [
                  { form_type: 'masu', value: '実装します' },
                  { form_type: 'nai', value: '実装しない' },
                ],
              },
            ],
            exampleCsv:
              'kanji,hiragana,meaning,han_viet,word_type,level,status,example\n実装する,じっそうする,Lập trình cài đặt chức năng,Thực trang,verb_3,N3,upload,仕様書に基づいてAPIを実装します。\n開発する,かいはつする,Phát triển hệ thống,Khai phát,verb_3,N3,upload,新機能を開発します。',
          }}
        />
      </div>
    </AdminLayout>
  );
}

