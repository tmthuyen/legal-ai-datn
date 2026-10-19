'use client';

import { Pencil, Trash2 } from 'lucide-react';
import type { ReactNode } from 'react';
import { EmptyState } from '@/components/common/EmptyState';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';

/** Cột dữ liệu khai báo 1 lần — DataTable tự render cả table (md+) lẫn card (mobile). */
export interface DataTableColumn<T> {
  key: string;
  header: string;
  className?: string;
  /** Ẩn cột này khỏi card view trên mobile (vd. cột phụ). */
  hideOnMobile?: boolean;
  render: (item: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  items: T[];
  rowKey: (item: T) => string | number;
  /** Hành động phụ trước Sửa/Xóa (vd. Phân quyền) — vẫn 1 điểm render. */
  extraActions?: Array<{
    label: string;
    icon: ReactNode;
    onClick: (item: T) => void;
    /** Ẩn nút với item cụ thể. */
    hide?: (item: T) => boolean;
  }>;
  /** Hiện cột hành động Sửa/Xóa — tránh lặp code ở mỗi trang. */
  onEdit?: (item: T) => void;
  onDelete?: (item: T) => void;
  /** Vô hiệu hóa hành động (vd. user không thể xóa chính mình). */
  canEdit?: (item: T) => boolean;
  canDelete?: (item: T) => boolean;
  /** Render gợi ý khi danh sách rỗng. */
  empty?: ReactNode;
  className?: string;
}

/**
 * Bảng dữ liệu CRUD dùng chung cho mọi trang admin (1 điểm render):
 * - `md+`: bảng shadcn (`overflow-x-auto` — không phá layout mobile).
 * - `<md`: danh sách card (mỗi hàng = label/value + hành động) — đúng chuẩn responsive.
 * Hành động Sửa/Xóa khai báo qua props, không lặp ở mỗi domain.
 */
export function DataTable<T>({
  columns,
  items,
  rowKey,
  extraActions,
  onEdit,
  onDelete,
  canEdit,
  canDelete,
  empty,
  className,
}: DataTableProps<T>) {
  const hasActions = Boolean(onEdit || onDelete || (extraActions && extraActions.length > 0));

  if (items.length === 0) {
    return <>{empty ?? <EmptyState title="Không có dữ liệu" description="Chưa có bản ghi nào." />}</>;
  }

  const renderActions = (item: T) => (
    <div className="flex items-center justify-end gap-1">
      {(extraActions ?? [])
        .filter((action) => !action.hide || !action.hide(item))
        .map((action) => (
          <Button
            key={action.label}
            variant="ghost"
            size="icon"
            className="size-9 cursor-pointer"
            onClick={() => action.onClick(item)}
            aria-label={action.label}
            title={action.label}
          >
            {action.icon}
          </Button>
        ))}
      {onEdit && (!canEdit || canEdit(item)) ? (
        <Button
          variant="ghost"
          size="icon"
          className="size-9 cursor-pointer"
          onClick={() => onEdit(item)}
          aria-label="Sửa"
          title="Sửa"
        >
          <Pencil className="size-4" aria-hidden="true" />
        </Button>
      ) : null}
      {onDelete && (!canDelete || canDelete(item)) ? (
        <Button
          variant="ghost"
          size="icon"
          className="text-destructive hover:text-destructive size-9 cursor-pointer"
          onClick={() => onDelete(item)}
          aria-label="Xóa"
          title="Xóa"
        >
          <Trash2 className="size-4" aria-hidden="true" />
        </Button>
      ) : null}
    </div>
  );

  return (
    <div className={cn('w-full space-y-3', className)}>
      {/* Bảng (md+) */}
      <div className="hidden overflow-x-auto rounded-xl border bg-card md:block">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => (
                <TableHead key={column.key} className={column.className}>
                  {column.header}
                </TableHead>
              ))}
              {hasActions ? (
                <TableHead className="text-right">Thao tác</TableHead>
              ) : null}
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <TableRow key={rowKey(item)}>
                {columns.map((column) => (
                  <TableCell key={column.key} className={column.className}>
                    {column.render(item)}
                  </TableCell>
                ))}
                {hasActions ? <TableCell className="text-right">{renderActions(item)}</TableCell> : null}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Card list (mobile) */}
      <ul className="space-y-2 md:hidden">
        {items.map((item) => (
          <li key={rowKey(item)} className="rounded-xl border bg-card p-3 text-sm">
            <dl className="space-y-1.5">
              {columns
                .filter((column) => !column.hideOnMobile)
                .map((column) => (
                  <div key={column.key} className="flex items-start justify-between gap-3">
                    <dt className="text-muted-foreground shrink-0">{column.header}</dt>
                    <dd className="min-w-0 truncate text-right">{column.render(item)}</dd>
                  </div>
                ))}
            </dl>
            {hasActions ? <div className="mt-2 flex justify-end border-t pt-2">{renderActions(item)}</div> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Skeleton bảng dùng chung khi lần đầu tải dữ liệu. */
export function CrudTableSkeleton({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="space-y-2" aria-hidden="true">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex items-center gap-4 rounded-xl border bg-card p-3">
          {Array.from({ length: columns }).map((_, columnIndex) => (
            <Skeleton
              key={columnIndex}
              className={cn('h-5 flex-1', columnIndex === columns - 1 && 'max-w-20')}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
