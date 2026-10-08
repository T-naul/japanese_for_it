'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { MaterialLesson, MaterialSection } from '@/types';
import { userMaterialsApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  BookOpen,
  FileText,
  ExternalLink,
  MessageSquare,
  HelpCircle,
  Info,
  Loader2,
} from 'lucide-react';

interface LessonReaderProps {
  materialId: string;
  lesson: MaterialLesson;
  sections: MaterialSection[];
  prevLessonId?: string | null;
  nextLessonId?: string | null;
  initialCompleted?: boolean;
  onCompletedChange?: (completed: boolean) => void;
}

export function LessonReader({
  materialId,
  lesson,
  sections,
  prevLessonId,
  nextLessonId,
  initialCompleted = false,
  onCompletedChange,
}: LessonReaderProps) {
  const [isCompleted, setIsCompleted] = useState<boolean>(initialCompleted || !!lesson.is_completed);
  const [isCompleting, setIsCompleting] = useState<boolean>(false);

  const handleComplete = async () => {
    setIsCompleting(true);
    try {
      const res = await userMaterialsApi.completeLesson(materialId, lesson.id);
      if (res && res.completed) {
        setIsCompleted(true);
        if (onCompletedChange) onCompletedChange(true);
      }
    } catch (err) {
      console.error('Failed to complete lesson:', err);
    } finally {
      setIsCompleting(false);
    }
  };

  const sortedSections = [...sections].sort((a, b) => a.order - b.order);

  return (
    <article className="space-y-8 max-w-3xl mx-auto">
      {/* Lesson Heading */}
      <header className="border-b border-stone-200/80 pb-6 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-bold tracking-wider text-stone-500 uppercase">
            Bài học số {lesson.lesson_number}
          </span>
          {isCompleted && (
            <Badge variant="success" className="gap-1 text-xs">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Đã hoàn thành</span>
            </Badge>
          )}
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight">
          {lesson.title || `Bài học ${lesson.lesson_number}`}
        </h1>

        {lesson.description && (
          <p className="text-sm text-stone-500 leading-relaxed">
            {lesson.description}
          </p>
        )}
      </header>

      {/* Sections in reading order */}
      <div className="space-y-6">
        {sortedSections.length === 0 ? (
          <div className="p-8 text-center bg-white rounded-2xl border border-stone-200 text-stone-400 text-sm">
            Nội dung bài học này đang được chuẩn bị.
          </div>
        ) : (
          sortedSections.map((sec) => (
            <SectionBlock key={sec.id} section={sec} />
          ))
        )}
      </div>

      {/* Bottom Completion & Navigation Actions */}
      <footer className="pt-8 pb-12 border-t border-stone-200/80 space-y-6">
        {/* Completion Action */}
        <div className="p-5 sm:p-6 rounded-2xl bg-white border border-stone-200 shadow-2xs flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="space-y-0.5 text-center sm:text-left">
            <h4 className="text-sm font-bold text-stone-900">
              {isCompleted ? 'Bài học đã hoàn thành' : 'Đánh dấu hoàn thành bài học?'}
            </h4>
            <p className="text-xs text-stone-500">
              {isCompleted
                ? 'Nội dung bài học này đã được lưu vào tiến độ học tập của bạn.'
                : 'Sau khi đọc và học xong, hãy nhấn nút bên dưới để ghi nhận tiến độ.'}
            </p>
          </div>

          <Button
            onClick={handleComplete}
            disabled={isCompleting}
            variant={isCompleted ? 'outline' : 'default'}
            size="default"
            className="w-full sm:w-auto font-semibold gap-2 shadow-xs"
          >
            {isCompleting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Đang lưu...</span>
              </>
            ) : isCompleted ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Đã hoàn thành</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4" />
                <span>Đánh dấu hoàn thành bài học</span>
              </>
            )}
          </Button>
        </div>

        {/* Prev / Next navigation */}
        <div className="flex items-center justify-between gap-3 pt-2">
          {prevLessonId ? (
            <Button asChild variant="outline" size="sm" className="gap-1.5 border-stone-200">
              <Link href={`/materials/${materialId}/lessons/${prevLessonId}`}>
                <ArrowLeft className="w-4 h-4" />
                <span>Bài trước</span>
              </Link>
            </Button>
          ) : (
            <div />
          )}

          <Button asChild variant="ghost" size="sm" className="text-xs text-stone-500">
            <Link href={`/materials/${materialId}`}>
              Quay lại danh sách bài học
            </Link>
          </Button>

          {nextLessonId ? (
            <Button asChild size="sm" className="gap-1.5 shadow-xs">
              <Link href={`/materials/${materialId}/lessons/${nextLessonId}`}>
                <span>Bài tiếp theo</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>
          ) : (
            <div />
          )}
        </div>
      </footer>
    </article>
  );
}

function SectionBlock({ section }: { section: MaterialSection }) {
  const type = section.section_type || 'text';

  // 1. Vocabulary Section
  if (type === 'vocabulary') {
    return (
      <div className="p-4 sm:p-5 rounded-xl bg-white border border-stone-200 shadow-2xs space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
              <BookOpen className="w-4 h-4" />
            </div>
            <span className="text-xs font-bold text-stone-700 uppercase tracking-wider">
              {section.title || 'Từ vựng (Vocabulary)'}
            </span>
          </div>

          {section.vocabulary && (
            <Link
              href={`/vocab?search=${encodeURIComponent(section.vocabulary.kanji || section.vocabulary.hiragana)}`}
              className="inline-flex items-center gap-1 text-[11px] text-indigo-600 hover:text-indigo-800 font-medium"
            >
              <span>Xem trong sổ từ vựng</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
          )}
        </div>

        {section.vocabulary ? (
          <div className="p-3 rounded-lg bg-stone-50 border border-stone-100 flex flex-wrap items-baseline justify-between gap-2">
            <div>
              <span className="text-base font-bold text-stone-900 mr-2">
                {section.vocabulary.kanji}
              </span>
              <span className="text-xs text-stone-500 font-mono">
                【{section.vocabulary.hiragana}】
              </span>
              <p className="text-xs text-stone-600 mt-1">
                {section.vocabulary.meaning}
              </p>
            </div>
            {section.vocabulary.level && (
              <Badge variant="outline" className="text-[10px]">
                {section.vocabulary.level}
              </Badge>
            )}
          </div>
        ) : null}

        {section.content && (
          <p className="text-sm text-stone-800 leading-relaxed whitespace-pre-line font-sans">
            {section.content}
          </p>
        )}
      </div>
    );
  }

  // 2. Grammar Section
  if (type === 'grammar') {
    return (
      <div className="p-4 sm:p-5 rounded-xl bg-white border border-stone-200 shadow-2xs space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-violet-50 text-violet-600">
              <FileText className="w-4 h-4" />
            </div>
            <span className="text-xs font-bold text-stone-700 uppercase tracking-wider">
              {section.title || 'Ngữ pháp (Grammar)'}
            </span>
          </div>

          {section.grammar && (
            <Link
              href={`/grammar?search=${encodeURIComponent(section.grammar.pattern)}`}
              className="inline-flex items-center gap-1 text-[11px] text-violet-600 hover:text-violet-800 font-medium"
            >
              <span>Xem trong sổ ngữ pháp</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
          )}
        </div>

        {section.grammar ? (
          <div className="p-3 rounded-lg bg-stone-50 border border-stone-100 space-y-1">
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-sm font-bold text-stone-900">
                {section.grammar.pattern}
              </span>
              {section.grammar.level && (
                <Badge variant="outline" className="text-[10px]">
                  {section.grammar.level}
                </Badge>
              )}
            </div>
            <p className="text-xs text-stone-600">
              {section.grammar.meaning}
            </p>
          </div>
        ) : null}

        {section.content && (
          <p className="text-sm text-stone-800 leading-relaxed whitespace-pre-line">
            {section.content}
          </p>
        )}
      </div>
    );
  }

  // 3. Dialogue Section
  if (type === 'dialogue') {
    return (
      <div className="p-4 sm:p-5 rounded-xl bg-white border border-stone-200 shadow-2xs space-y-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
            <MessageSquare className="w-4 h-4" />
          </div>
          <span className="text-xs font-bold text-stone-700 uppercase tracking-wider">
            {section.title || 'Hội thoại thực tế (Dialogue)'}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-stone-50/70 border border-stone-100 text-sm text-stone-900 leading-relaxed whitespace-pre-line font-sans">
          {section.content}
        </div>
      </div>
    );
  }

  // 4. Exercise Section
  if (type === 'exercise') {
    return (
      <div className="p-4 sm:p-5 rounded-xl bg-amber-50/30 border border-amber-200/80 space-y-2">
        <div className="flex items-center gap-2 text-amber-800">
          <HelpCircle className="w-4 h-4" />
          <span className="text-xs font-bold uppercase tracking-wider">
            {section.title || 'Bài tập vận dụng (Exercise)'}
          </span>
        </div>
        <p className="text-sm text-stone-800 leading-relaxed whitespace-pre-line">
          {section.content}
        </p>
      </div>
    );
  }

  // 5. Note or Explanation
  if (type === 'note' || type === 'explanation') {
    return (
      <div className="p-4 sm:p-5 rounded-xl bg-stone-50 border border-stone-200/80 space-y-2">
        <div className="flex items-center gap-2 text-stone-600">
          <Info className="w-4 h-4" />
          <span className="text-xs font-bold uppercase tracking-wider">
            {section.title || 'Ghi chú & Giải thích (Note)'}
          </span>
        </div>
        <p className="text-sm text-stone-700 leading-relaxed whitespace-pre-line">
          {section.content}
        </p>
      </div>
    );
  }

  // Default: Standard Text / Reading / Custom Section
  return (
    <div className="space-y-2">
      {section.title && (
        <h3 className="text-base sm:text-lg font-bold text-stone-900 tracking-tight">
          {section.title}
        </h3>
      )}
      <p className="text-base text-stone-800 leading-relaxed whitespace-pre-line font-sans">
        {section.content}
      </p>
    </div>
  );
}
