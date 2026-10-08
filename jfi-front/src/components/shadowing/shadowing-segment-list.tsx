'use client';

import React from 'react';
import { ShadowingSegment, UserShadowingSegment } from '@/types';
import { CheckCircle2, Play, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ShadowingSegmentListProps {
  segments: ShadowingSegment[];
  currentSegment?: ShadowingSegment | null;
  userSegments?: UserShadowingSegment[];
  onSelectSegment: (segment: ShadowingSegment) => void;
}

function formatSecs(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

export function ShadowingSegmentList({
  segments,
  currentSegment,
  userSegments = [],
  onSelectSegment,
}: ShadowingSegmentListProps) {
  const completedMap = new Map<number, boolean>();
  userSegments.forEach((us) => {
    completedMap.set(us.sequence, us.is_completed);
  });

  const sorted = [...segments].sort((a, b) => a.sequence - b.sequence);

  if (sorted.length === 0) {
    return (
      <div className="p-8 text-center bg-white rounded-2xl border border-stone-200 text-stone-400 text-sm">
        Video này chưa có dữ liệu câu thoại (segments).
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {sorted.map((seg) => {
        const isCurrent = currentSegment?.id === seg.id;
        const isCompleted = completedMap.get(seg.sequence) === true;

        return (
          <button
            key={seg.id}
            type="button"
            onClick={() => onSelectSegment(seg)}
            className={cn(
              'w-full text-left p-3.5 sm:p-4 rounded-xl border transition-all flex items-start justify-between gap-3 cursor-pointer group',
              isCurrent
                ? 'border-indigo-300 bg-indigo-50/50 shadow-2xs'
                : 'border-stone-200/80 bg-white hover:bg-stone-50/80'
            )}
          >
            <div className="flex items-start gap-3 min-w-0">
              {/* Sequence / State icon */}
              <div
                className={cn(
                  'w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 mt-0.5',
                  isCurrent
                    ? 'bg-indigo-600 text-white shadow-2xs'
                    : isCompleted
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-stone-100 text-stone-600'
                )}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : (
                  <span>{seg.sequence}</span>
                )}
              </div>

              {/* Text & Timing */}
              <div className="min-w-0 space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono text-stone-400">
                    {formatSecs(seg.start_time)} - {formatSecs(seg.end_time)}
                  </span>
                  {/* Non-color indicator for current segment */}
                  {isCurrent && (
                    <span className="text-[10px] font-bold text-indigo-700 bg-indigo-100/90 px-1.5 py-0.2 rounded font-sans flex items-center gap-1">
                      <span>▶</span>
                      <span>Đang phát</span>
                    </span>
                  )}
                  {isCompleted && (
                    <span className="text-[10px] font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded font-sans">
                      ✓ Đã xong
                    </span>
                  )}
                </div>

                <p className="text-sm font-bold text-stone-900 group-hover:text-indigo-600 transition-colors line-clamp-1">
                  {seg.text || '(Chưa có nội dung văn bản)'}
                </p>

                {seg.reading && seg.reading !== seg.text && (
                  <p className="text-xs text-stone-400 line-clamp-1 font-mono">
                    {seg.reading}
                  </p>
                )}
              </div>
            </div>

            <ChevronRight className="w-4 h-4 text-stone-300 group-hover:text-stone-600 shrink-0 mt-2 transition-colors" />
          </button>
        );
      })}
    </div>
  );
}
