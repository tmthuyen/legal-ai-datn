'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface DataPaginationProps {
  page: number;
  totalPages: number;
  /** Tổng số bản ghi (tuỳ chọn) để hiển thị "N kết quả". */
  total?: number;
  onPageChange: (page: number) => void;
  className?: string;
  /** Vô hiệu hoá toàn bộ nút (ví dụ khi đang tải). */
  disabled?: boolean;
  ariaLabel?: string;
}

/** Dựng dải số trang: 1 … (current-1, current, current+1) … total */
function getPageItems(current: number, total: number): (number | 'ellipsis')[] {
  if (total <= 1) return [1];

  const items: (number | 'ellipsis')[] = [];
  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);

  items.push(1);
  if (start > 2) items.push('ellipsis');
  for (let pageNumber = start; pageNumber <= end; pageNumber++) {
    items.push(pageNumber);
  }
  if (end < total - 1) items.push('ellipsis');
  items.push(total);

  return items;
}

/**
 * Phân trang dùng chung (presentational) — mọi biến thể (server/client) tái sử dụng
 * component này thay vì tự viết lại control. Touch target ≥ 44px (FRONTEND_RULES §4).
 */
export function DataPagination({
  page,
  totalPages,
  total,
  onPageChange,
  className,
  disabled = false,
  ariaLabel = 'Phân trang',
}: DataPaginationProps) {
  if (totalPages <= 1) return null;

  const items = getPageItems(page, totalPages);

  return (
    <nav
      aria-label={ariaLabel}
      className={cn(
        'mt-8 flex flex-col items-center justify-between gap-4 border-t pt-4 sm:flex-row',
        className,
      )}
    >
      <p className="text-muted-foreground text-sm">
        Trang <span className="text-foreground font-semibold">{page}</span> / {totalPages}
        {typeof total === 'number' ? <span> — {total} kết quả</span> : null}
      </p>

      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          className="size-11"
          disabled={disabled || page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Trang trước"
        >
          <ChevronLeft />
        </Button>

        {items.map((item, index) =>
          item === 'ellipsis' ? (
            <span key={`ellipsis-${index}`} className="text-muted-foreground px-1">
              …
            </span>
          ) : (
            <Button
              key={item}
              variant={item === page ? 'default' : 'outline'}
              size="icon"
              className="size-11"
              disabled={disabled}
              onClick={() => onPageChange(item)}
              aria-current={item === page ? 'page' : undefined}
            >
              {item}
            </Button>
          ),
        )}

        <Button
          variant="outline"
          size="icon"
          className="size-11"
          disabled={disabled || page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Trang sau"
        >
          <ChevronRight />
        </Button>
      </div>
    </nav>
  );
}
