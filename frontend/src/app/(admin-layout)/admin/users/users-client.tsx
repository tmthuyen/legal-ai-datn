'use client';

import { useEffect, useState } from 'react';
import { Lock } from 'lucide-react';
import { CrudToolbar } from '@/components/admin/crud-toolbar';
import { CrudTableSkeleton, DataTable, DataTableColumn } from '@/components/admin/data-table';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { DataPagination } from '@/components/common/DataPagination';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { Badge } from '@/components/ui/badge';
import { useAdminUsers, useUpdateUserStatus } from '@/hooks/tankstack/useAdminAnalytics';
import { LegalUser } from '@/shared/types/legal.types';
import { useAuthStore } from '@/stores/auth.store';
import dateTimeUtils from '@/shared/utils/formatting';

/**
 * Bảng quản lý người dùng (contract §4.4): danh sách phân trang + tìm kiếm theo
 * email/username, khóa/mở khóa tài khoản (`PUT /admin/users/:id/status`).
 * Không có API tạo/sửa/xóa user ở tầng Services nên UI không cung cấp.
 */
export function UsersClient() {
  const currentUser = useAuthStore((state) => state.user);

  const [page, setPage] = useState(1);
  const [keywordInput, setKeywordInput] = useState('');
  const [search, setSearch] = useState('');
  const [statusTarget, setStatusTarget] = useState<LegalUser | null>(null);

  // Debounce ô tìm kiếm, đưa về trang 1 khi từ khóa đổi.
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(keywordInput.trim());
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [keywordInput]);

  const list = useAdminUsers({ page, limit: 10, search });
  const updateStatus = useUpdateUserStatus();

  const selfId = currentUser?.id;
  const items = list.data?.items ?? [];

  const columns: DataTableColumn<LegalUser>[] = [
    {
      key: 'username',
      header: 'Tên đăng nhập',
      render: (user) => <span className="font-medium">{user.username}</span>,
    },
    { key: 'email', header: 'Email', render: (user) => user.email },
    {
      key: 'fullName',
      header: 'Họ tên',
      hideOnMobile: true,
      render: (user) => user.fullName || '—',
    },
    {
      key: 'role',
      header: 'Vai trò',
      className: 'w-28',
      render: (user) => (
        <Badge variant={user.role === 'admin' ? 'destructive' : 'secondary'} className="uppercase">
          {user.role}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      className: 'w-32',
      render: (user) => (
        <Badge variant={user.isActive ? 'default' : 'outline'}>
          {user.isActive ? 'Hoạt động' : 'Đã khóa'}
        </Badge>
      ),
    },
    {
      key: 'createdAt',
      header: 'Ngày tạo',
      hideOnMobile: true,
      render: (user) => dateTimeUtils.formatShortDate(user.createdAt),
    },
  ];

  const confirmStatusChange = async () => {
    if (!statusTarget) return;
    await updateStatus.mutateAsync({ id: statusTarget.id, isActive: !statusTarget.isActive });
    setStatusTarget(null);
  };

  return (
    <div className="flex w-full flex-col gap-4">
      <CrudToolbar
        keyword={keywordInput}
        onKeywordChange={setKeywordInput}
        searchPlaceholder="Tìm theo email hoặc tên đăng nhập…"
        onAdd={() => {}}
        hideAdd
      />

      {list.isLoading ? (
        <CrudTableSkeleton />
      ) : list.isError ? (
        <ErrorState
          title="Không thể tải danh sách người dùng"
          description="Vui lòng kiểm tra kết nối và thử lại."
          onRetry={() => list.refetch()}
        />
      ) : (
        <>
          <DataTable
            columns={columns}
            items={items}
            rowKey={(user) => user.id}
            extraActions={[
              {
                label: 'Khóa/Mở khóa',
                icon: <Lock className="size-4" aria-hidden="true" />,
                onClick: (user) => setStatusTarget(user),
                hide: (user) => user.id === selfId,
              },
            ]}
            empty={
              <EmptyState
                title="Không có người dùng nào"
                description="Kiểm tra lại bộ lọc tìm kiếm."
              />
            }
          />
          {list.data ? (
            <DataPagination
              page={list.data.pagination.page}
              totalPages={list.data.pagination.totalPages}
              total={list.data.pagination.total}
              onPageChange={setPage}
              disabled={list.isFetching}
              ariaLabel="Phân trang người dùng"
            />
          ) : null}
        </>
      )}

      <ConfirmDialog
        isOpen={statusTarget !== null}
        variant={statusTarget?.isActive ? 'destructive' : 'default'}
        title={statusTarget?.isActive ? 'Khóa tài khoản' : 'Mở khóa tài khoản'}
        description={
          statusTarget?.isActive
            ? `Bạn có chắc muốn khóa tài khoản "${statusTarget?.username ?? ''}"? Người dùng sẽ không thể đăng nhập.`
            : `Bạn có chắc muốn mở khóa tài khoản "${statusTarget?.username ?? ''}"?`
        }
        confirmText={statusTarget?.isActive ? 'Khóa' : 'Mở khóa'}
        onConfirm={confirmStatusChange}
        onCancel={() => setStatusTarget(null)}
      />
    </div>
  );
}
