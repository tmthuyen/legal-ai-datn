'use client';

import { useMemo, useState } from 'react';
import { KeyRound } from 'lucide-react';
import { AssignRolesDialog } from '@/components/admin/assign-roles-dialog';
import { CrudToolbar } from '@/components/admin/crud-toolbar';
import { CrudTableSkeleton, DataTable, DataTableColumn } from '@/components/admin/data-table';
import { CrudDeleteDialog } from '@/components/admin/delete-dialog';
import { CrudFormDialog, CrudFormField, useCrudFormValues } from '@/components/admin/form-dialog';
import { DataPagination } from '@/components/common/DataPagination';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { Badge } from '@/components/ui/badge';
import { AdminUserInput, adminUsers } from '@/hooks/tankstack/admin';
import { useCrudPage } from '@/hooks/tankstack/admin-crud';
import { User } from '@/shared/types/api.types';
import { useAuthStore } from '@/stores/auth.store';
import { z } from 'zod';

type UserForm = Record<string, unknown>;

/** Form khi sửa — backend `PUT /users/:id` (`UpdateProfileDto`) chỉ nhận `fullName` ở đây. */
const EDIT_FIELDS: CrudFormField[] = [{ name: 'fullName', label: 'Họ tên', placeholder: 'Nguyễn Văn A' }];

const CREATE_FIELDS: CrudFormField[] = [
  { name: 'email', label: 'Email', placeholder: 'user@example.com' },
  { name: 'fullName', label: 'Họ tên', placeholder: 'Nguyễn Văn A' },
  { name: 'password', label: 'Mật khẩu', placeholder: 'Tối thiểu 8 ký tự' },
  { name: 'confirmPassword', label: 'Nhập lại mật khẩu' },
];

const editSchema = z.object({
  fullName: z.string().min(1, 'Họ tên là bắt buộc'),
}) as unknown as z.ZodType<UserForm>;

const createSchema = z
  .object({
    email: z.string().min(1, 'Email là bắt buộc').email('Email không hợp lệ'),
    fullName: z.string().min(1, 'Họ tên là bắt buộc'),
    password: z.string().min(8, 'Mật khẩu tối thiểu 8 ký tự'),
    confirmPassword: z.string().min(1, 'Vui lòng nhập lại mật khẩu'),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: 'Mật khẩu không khớp',
    path: ['confirmPassword'],
  }) as unknown as z.ZodType<UserForm>;

const COLUMNS: DataTableColumn<User>[] = [
  {
    key: 'fullName',
    header: 'Họ tên',
    render: (user) => <span className="font-medium">{user.fullName || '—'}</span>,
  },
  { key: 'email', header: 'Email', render: (user) => user.email },
  {
    key: 'status',
    header: 'Trạng thái',
    className: 'w-28',
    render: (user) => (
      <Badge variant="outline" className="capitalize">
        {user.status || 'unknown'}
      </Badge>
    ),
  },
  {
    key: 'roles',
    header: 'Vai trò',
    render: (user) =>
      user.roles?.length ? (
        <div className="flex flex-wrap gap-1">
          {user.roles.map((role) => (
            <Badge key={role.id} variant="secondary">
              {role.name}
            </Badge>
          ))}
        </div>
      ) : (
        <span className="text-muted-foreground">—</span>
      ),
  },
];

/** CRUD Người dùng — form thêm/sửa khác nhau theo mode + dialog phân quyền tái sử dụng CrudFormDialog. */
export function UsersClient() {
  const currentUser = useAuthStore((state) => state.user);
  const [roleTarget, setRoleTarget] = useState<User | null>(null);

  const mutations = {
    create: adminUsers.useCreate(),
    update: adminUsers.useUpdate(),
    remove: adminUsers.useDelete(),
  };
  const state = useCrudPage<User, AdminUserInput>(mutations);
  const list = adminUsers.useList({ page: state.page, limit: 10, keyword: state.keyword });

  const fields = state.editing ? EDIT_FIELDS : CREATE_FIELDS;
  const schema = state.editing ? editSchema : createSchema;
  const defaultValues = useCrudFormValues<UserForm>(fields, state.editing);

  const handleSubmit = (values: UserForm) => {
    if (state.editing) {
      state.submit({ fullName: String(values.fullName ?? '') });
      return;
    }
    state.submit({
      email: String(values.email ?? ''),
      fullName: String(values.fullName ?? ''),
      password: String(values.password ?? ''),
      confirmPassword: String(values.confirmPassword ?? ''),
    });
  };

  const selfId = currentUser?.id;
  const title = useMemo(
    () => (state.editing ? 'Sửa người dùng' : 'Thêm người dùng'),
    [state.editing],
  );

  return (
    <div className="flex w-full flex-col gap-4">
      <CrudToolbar
        keyword={state.keywordInput}
        onKeywordChange={state.setKeywordInput}
        searchPlaceholder="Tìm theo tên hoặc email…"
        onAdd={state.openCreate}
        addLabel="Thêm người dùng"
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
            columns={COLUMNS}
            items={list.data?.items ?? []}
            rowKey={(user) => user.id}
            extraActions={[
              {
                label: 'Phân quyền',
                icon: <KeyRound className="size-4" aria-hidden="true" />,
                onClick: (user) => setRoleTarget(user),
              },
            ]}
            onEdit={state.openEdit}
            onDelete={(user) => state.setDeleteTarget(user)}
            canDelete={(user) => user.id !== selfId}
            empty={
              <EmptyState
                title="Không có người dùng nào"
                description="Thêm người dùng đầu tiên hoặc kiểm tra bộ lọc tìm kiếm."
              />
            }
          />
          {list.data ? (
            <DataPagination
              page={list.data.pagination.page}
              totalPages={list.data.pagination.totalPages}
              total={list.data.pagination.total}
              onPageChange={state.setPage}
              disabled={list.isFetching}
              ariaLabel="Phân trang người dùng"
            />
          ) : null}
        </>
      )}

      <CrudFormDialog
        open={state.dialogOpen}
        onOpenChange={state.setDialogOpen}
        title={title}
        schema={schema}
        fields={fields}
        defaultValues={defaultValues}
        onSubmit={handleSubmit}
        submitting={state.saving}
      />

      <AssignRolesDialog user={roleTarget} onCancel={() => setRoleTarget(null)} />

      <CrudDeleteDialog
        target={
          state.deleteTarget
            ? {
              id: state.deleteTarget.id,
              label: state.deleteTarget.fullName || state.deleteTarget.email,
            }
            : null
        }
        onCancel={() => state.setDeleteTarget(null)}
        onConfirm={state.confirmDelete}
        isPending={state.deleting}
        entityLabel="người dùng"
      />
    </div>
  );
}
