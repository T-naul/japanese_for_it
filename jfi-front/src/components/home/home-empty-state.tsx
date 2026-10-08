'use client';

import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, RotateCcw } from 'lucide-react';

interface HomeErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function HomeErrorState({
  message = 'Không thể đồng bộ dữ liệu học tập với máy chủ.',
  onRetry,
}: HomeErrorStateProps) {
  return (
    <Card className="border-amber-200/80 bg-amber-50/40 p-6 text-center space-y-3 rounded-2xl">
      <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center mx-auto">
        <AlertCircle className="w-5 h-5" />
      </div>
      <div>
        <h3 className="text-sm font-bold text-stone-900">
          Chưa đồng bộ được dữ liệu học tập
        </h3>
        <p className="text-xs text-stone-500 mt-1 max-w-sm mx-auto leading-relaxed">
          {message}
        </p>
      </div>
      {onRetry && (
        <div className="pt-1">
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="text-xs gap-1.5 h-8 border-amber-200 text-amber-800 hover:bg-amber-100"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Thử lại</span>
          </Button>
        </div>
      )}
    </Card>
  );
}
