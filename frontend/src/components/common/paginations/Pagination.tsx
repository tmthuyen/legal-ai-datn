'use client';

import { useState, type ComponentType } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { RotateCw } from 'lucide-react';
import { DataPagination } from '@/components/common/DataPagination';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { Card } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import type { ApiPaginatedResponse } from '@/shared/types/api.types';

interface PaginatedTableProps<T> {
  queryKeyName: string;
  /** Trả về envelope backend: `{ result, pagination: { total, page, limit, totalPages } }`. */
  fetchFn: (page: number, limit: number) => Promise<ApiPaginatedResponse<T[]>>;
  ContentComponent: ComponentType<{ data: T[] }>;
  title?: string;
  staleTime?: number;
  gcTime?: number;
  pageSizeOptions?: number[];
}

const LoadingPagination = () => (
  <Card className="flex flex-col gap-8 border border-gray-100 bg-white p-4 py-8 md:p-6 dark:border-slate-700 dark:bg-slate-800">
    <Skeleton className="h-16 w-1/3 rounded-lg" />
    <Skeleton className="h-64 w-full rounded-lg" />
    <Skeleton className="h-16 w-full rounded-lg" />
  </Card>
);

/**
 * Khung danh sách **server-side pagination** dùng chung cho khu vực admin:
 * tự gọi API theo `page/limit` và tái sử dụng `DataPagination` / `EmptyState` / `ErrorState`.
 */
export function PaginatedTable<T>({
  queryKeyName,
  fetchFn,
  ContentComponent,
  title,
  staleTime,
  gcTime,
  pageSizeOptions = [5, 10, 20, 50],
}: PaginatedTableProps<T>) {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(5);

  const { data, refetch, isPending, isError } = useQuery({
    queryKey: [queryKeyName, page, limit],
    queryFn: () => fetchFn(page, limit),
    placeholderData: keepPreviousData,
    staleTime: staleTime ?? 60 * 1000,
    gcTime: gcTime ?? 5 * 60 * 1000,
  });

  if (isPending) return <LoadingPagination />;
  if (isError) return <ErrorState title="Không thể tải dữ liệu" onRetry={() => refetch()} />;

  const items = data?.result ?? [];
  const pagination = data?.pagination;

  return (
    <Card className="border border-gray-100 bg-white p-4 py-8 md:p-6 dark:border-slate-700 dark:bg-slate-800">
      <div className="flex w-full items-center gap-2">
        {title ? <h2 className="text-xl font-bold">{title}</h2> : null}

        <button
          type="button"
          className="border-primary dark:border-primary/10 bg-primary/10 dark:bg-primary/5 text-primary hover:bg-primary/20 hover:dark:bg-primary/10 ms-auto flex cursor-pointer items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-bold shadow-sm backdrop-blur-md transition-all active:scale-95 hover:shadow-md"
          onClick={() => refetch()}
        >
          <RotateCw className="h-4 w-4" />
          Tải lại
        </button>
      </div>

      {items.length === 0 ? (
        <EmptyState className="mt-6" title="Chưa có dữ liệu" />
      ) : (
        <ContentComponent data={items} />
      )}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span className="font-medium">Hiển thị</span>
          <Select
            value={String(pagination?.limit ?? limit)}
            onValueChange={(val) => {
              setLimit(Number(val));
              setPage(1);
            }}
          >
            <SelectTrigger className="h-8 w-20">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {pageSizeOptions.map((option) => (
                <SelectItem key={option} value={String(option)}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="font-medium">/ trang</span>

          {typeof pagination?.total === 'number' ? (
            <span className="font-medium">Tổng số: {pagination.total}</span>
          ) : null}
        </div>

        {pagination ? (
          <DataPagination
            className="mt-0 border-t-0 pt-0"
            page={pagination.page}
            totalPages={pagination.totalPages}
            onPageChange={setPage}
          />
        ) : null}
      </div>
    </Card>
  );
}
