'use client';

import React, { useState } from 'react';
import { Upload, X, CheckCircle2, AlertTriangle, Download, RefreshCw, FileSpreadsheet } from 'lucide-react';
import { ImportResult } from '@/types';

interface FileImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description: string;
  onUpload: (file: File) => Promise<ImportResult>;
  onSuccess: () => void;
  sampleInfo: {
    filenamePrefix: string;
    headers: string[];
    exampleJson: object[];
    exampleCsv: string;
  };
}

export default function FileImportModal({
  isOpen,
  onClose,
  title,
  description,
  onUpload,
  onSuccess,
  sampleInfo,
}: FileImportModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [showSample, setShowSample] = useState(false);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setError(null);
      setResult(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Vui lòng chọn một file (.json, .csv, hoặc .xlsx)');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await onUpload(file);
      setResult(res);
      if (res.created_count > 0) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message || 'Đã xảy ra lỗi khi upload file.');
    } finally {
      setLoading(false);
    }
  };

  const downloadSampleJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(sampleInfo.exampleJson, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `${sampleInfo.filenamePrefix}_template.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const downloadSampleCsv = () => {
    const dataStr = 'data:text/csv;charset=utf-8,' + encodeURIComponent(sampleInfo.exampleCsv);
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `${sampleInfo.filenamePrefix}_template.csv`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const resetModal = () => {
    setFile(null);
    setError(null);
    setResult(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-5 my-8">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-indigo-400" />
              {title}
            </h3>
            <p className="text-xs text-slate-400 mt-1">{description}</p>
          </div>
          <button
            onClick={() => {
              resetModal();
              onClose();
            }}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Sample Templates Bar */}
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
          <span className="text-slate-400">Tải file mẫu định dạng chuẩn:</span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={downloadSampleJson}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-indigo-300 font-medium flex items-center gap-1.5 transition"
            >
              <Download className="w-3.5 h-3.5" />
              File JSON Mẫu
            </button>
            <button
              type="button"
              onClick={downloadSampleCsv}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-300 font-medium flex items-center gap-1.5 transition"
            >
              <Download className="w-3.5 h-3.5" />
              File CSV Mẫu
            </button>
            <button
              type="button"
              onClick={() => setShowSample(!showSample)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            >
              {showSample ? 'Ẩn Cấu Trúc' : 'Xem Cấu Trúc File'}
            </button>
          </div>
        </div>

        {/* Format Guide */}
        {showSample && (
          <div className="p-4 rounded-xl bg-slate-950 border border-indigo-500/20 text-xs space-y-2 font-mono">
            <div className="text-indigo-400 font-bold font-sans">Các cột / thuộc tính được hỗ trợ:</div>
            <div className="text-slate-300 flex flex-wrap gap-1">
              {sampleInfo.headers.map((h) => (
                <span key={h} className="px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                  {h}
                </span>
              ))}
            </div>
            <div className="text-slate-400 text-[11px] pt-1 font-sans">
              * Hệ thống backend sẽ tự động kiểm tra định dạng và bỏ qua dòng trống.
            </div>
          </div>
        )}

        {/* Global Error Banner */}
        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* File Dropzone */}
        {!result && (
          <form onSubmit={handleUploadSubmit} className="space-y-4">
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className="border-2 border-dashed border-slate-700 hover:border-indigo-500/50 rounded-2xl p-8 text-center bg-slate-950/40 hover:bg-slate-950/80 transition cursor-pointer relative"
            >
              <input
                type="file"
                accept=".json,.csv,.xlsx,.xls"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
              <div className="flex flex-col items-center justify-center space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
                  <Upload className="w-6 h-6" />
                </div>
                {file ? (
                  <div>
                    <p className="font-semibold text-white text-sm">{file.name}</p>
                    <p className="text-xs text-slate-400 mt-0.5 font-mono">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-semibold text-slate-200">
                      Kéo thả file vào đây hoặc <span className="text-indigo-400 underline">chọn file</span>
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      Hỗ trợ các định dạng: <b>.json</b>, <b>.csv</b>, <b>.xlsx</b>
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  resetModal();
                  onClose();
                }}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-sm font-medium hover:bg-slate-700 transition"
              >
                Hủy
              </button>
              <button
                type="submit"
                disabled={!file || loading}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/30 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2"
              >
                {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
                {loading ? 'Đang Xử Lý & Validate...' : 'Tải Lên & Thêm Mới'}
              </button>
            </div>
          </form>
        )}

        {/* Results Overview */}
        {result && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between text-sm font-bold">
                <span className="text-white flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  Kết Quả Import
                </span>
                <span className="text-xs text-slate-400 font-normal">
                  Tổng số dòng: <b className="text-white">{result.total_rows}</b>
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  <div className="font-semibold text-lg">{result.created_count}</div>
                  <div>Tạo mới thành công</div>
                </div>
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
                  <div className="font-semibold text-lg">{result.error_count}</div>
                  <div>Dòng gặp lỗi validate</div>
                </div>
              </div>
            </div>

            {/* Error List */}
            {result.errors.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider">
                  Chi Tiết Dòng Không Hợp Lệ ({result.errors.length}):
                </h4>
                <div className="max-h-48 overflow-y-auto rounded-xl bg-slate-950 border border-slate-800 divide-y divide-slate-800/60">
                  {result.errors.map((errItem, idx) => (
                    <div key={idx} className="p-3 text-xs space-y-1">
                      <div className="flex items-center justify-between text-slate-300">
                        <span className="font-bold text-indigo-400">Dòng {errItem.row}</span>
                        <span className="font-mono text-slate-400 truncate max-w-[200px]">
                          {errItem.kanji || errItem.pattern || ''}
                        </span>
                      </div>
                      <ul className="list-disc list-inside text-rose-400/90 text-[11px] space-y-0.5">
                        {errItem.errors.map((msg, mIdx) => (
                          <li key={mIdx}>{msg}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={resetModal}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-sm font-medium hover:bg-slate-700 transition"
              >
                Upload File Khác
              </button>
              <button
                type="button"
                onClick={() => {
                  resetModal();
                  onClose();
                }}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/30 transition"
              >
                Hoàn Tất
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
