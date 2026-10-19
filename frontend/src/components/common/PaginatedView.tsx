'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { DataPagination } from '@/components/common/DataPagination';

interface PaginatedViewProps<T> {
  data: T[];
  itemsPerPage?: number;
  renderContent: (paginatedData: T[]) => ReactNode;
  /** Reset về trang 1 khi phụ thuộc (bộ lọc) thay đổi. */
  resetDependency?: unknown;
}

/**
 * Phân trang **client-side** cho danh sách đã có sẵn toàn bộ dữ liệu.
 * Tái sử dụng `DataPagination` để không tự viết lại control phân trang.
 */
export function PaginatedView<T>({
  data,
  itemsPerPage = 5,
  renderContent,
  resetDependency,
}: PaginatedViewProps<T>) {
  const [currentPage, setCurrentPage] = useState(1);
  const totalPages = Math.max(1, Math.ceil(data.length / itemsPerPage));

  const paginatedData = data.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  useEffect(() => {
    setCurrentPage(1);
  }, [resetDependency]);

  return (
    <div className="w-full">
      {renderContent(paginatedData)}

      <DataPagination
        page={currentPage}
        totalPages={totalPages}
        total={data.length}
        onPageChange={setCurrentPage}
      />
    </div>
  );
}
