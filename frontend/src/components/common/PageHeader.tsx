import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description?: string;
  /** Vùng hành động bên phải tiêu đề (nút/link). */
  actions?: ReactNode;
  className?: string;
}

/**
 * Tiêu đề trang dùng chung — thay cho block `text-3xl font-extrabold` bị lặp ở nhiều trang.
 * Typography bám đúng quy ước project (FRONTEND_RULES §3).
 */
export function PageHeader({ title, description, actions, className }: PageHeaderProps) {
  return (
    <div className={cn('flex flex-wrap items-start justify-between gap-3', className)}>
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white">{title}</h1>
        {description ? <p className="text-gray-500 dark:text-gray-400">{description}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}
