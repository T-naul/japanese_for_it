'use client';

import React from 'react';
import { ShadowingSegment } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Volume2, User } from 'lucide-react';

interface ShadowingSentenceProps {
  segment?: ShadowingSegment | null;
  totalSegments?: number;
  onReplay?: () => void;
}

export function ShadowingSentence({
  segment,
  totalSegments = 0,
  onReplay,
}: ShadowingSentenceProps) {
  if (!segment) {
    return (
      <div className="p-8 text-center bg-white rounded-2xl border border-stone-200 text-stone-400 text-sm">
        Chọn một câu thoại trong danh sách bên dưới để bắt đầu luyện tập.
      </div>
    );
  }

  const hasReading = !!segment.reading && segment.reading.trim() !== '' && segment.reading !== segment.text;
  const hasText = !!segment.text && segment.text.trim() !== '';

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-white border border-stone-200/90 shadow-2xs space-y-4">
      <div className="flex items-center justify-between gap-2 border-b border-stone-100 pb-3">
        <div className="flex items-center gap-2">
          <Badge variant="subtle" className="font-semibold text-xs text-indigo-700 bg-indigo-50 border-indigo-200/60">
            Câu {segment.sequence} {totalSegments > 0 ? `/ ${totalSegments}` : ''}
          </Badge>

          {segment.speaker && (
            <span className="text-xs text-stone-500 flex items-center gap-1">
              <User className="w-3.5 h-3.5 text-stone-400" />
              <span>{segment.speaker}</span>
            </span>
          )}
        </div>

        {onReplay && (
          <button
            type="button"
            onClick={onReplay}
            title="Nghe lại câu này"
            className="p-1.5 rounded-lg text-stone-400 hover:text-indigo-600 hover:bg-stone-50 transition-colors"
          >
            <Volume2 className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="space-y-2 py-1 text-center sm:text-left">
        {/* Furigana / Reading */}
        {hasReading && (
          <p className="text-sm sm:text-base text-stone-500 font-mono tracking-wide">
            {segment.reading}
          </p>
        )}

        {/* Main Japanese Sentence */}
        <h3 className="text-xl sm:text-2xl md:text-3xl font-extrabold text-stone-900 tracking-tight leading-relaxed font-sans">
          {hasText ? segment.text : '(Không có văn bản hiển thị)'}
        </h3>
      </div>
    </div>
  );
}
