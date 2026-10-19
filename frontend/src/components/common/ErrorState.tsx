'use client';

import { AlertTriangle, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface ErrorStateProps {
  title?: string;
  description?: string;
  /** Nếu có, hiển thị nút thử lại. */
  onRetry?: () => void;
  retryText?: string;
  /** Hành động tuỳ biến (dùng thay cho nút thử lại). */
  action?: ReactNode;
  className?: string;
}

/** Trạng thái lỗi dùng chung cho mọi vùng dữ liệu. */
export function ErrorState({
  title = 'Đã có lỗi xảy ra',
  description = 'Không thể tải dữ liệu. Vui lòng thử lại.',
  onRetry,
  retryText = 'Thử lại',
  action,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed p-10 text-center',
        className,
      )}
    >
      <AlertTriangle className="text-destructive size-10" aria-hidden />
      <p className="text-foreground font-medium">{title}</p>
      {description ? <p className="text-muted-foreground max-w-md text-sm">{description}</p> : null}
      {onRetry ? (
        <Button variant="outline" onClick={onRetry}>
          <RefreshCcw /> {retryText}
        </Button>
      ) : (
        action
      )}
    </div>
  );
}
