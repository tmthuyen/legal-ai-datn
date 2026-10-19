import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface SectionHeaderProps {
  title: string;
  description?: string;
  /** Vùng hành động bên phải (nút/link "Xem tất cả"...). */
  action?: ReactNode;
  className?: string;
}

/** Tiêu đề một mục trong trang (dùng chung, không tự viết lại markup). */
export function SectionHeader({ title, description, action, className }: SectionHeaderProps) {
  return (
    <div className={cn('flex flex-wrap items-end justify-between gap-3', className)}>
      <div className="space-y-1">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{title}</h2>
        {description ? <p className="text-gray-500 dark:text-gray-400">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
