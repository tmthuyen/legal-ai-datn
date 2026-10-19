'use client';

import { CrudToolbar } from '@/components/admin/crud-toolbar';
import { CrudTableSkeleton, DataTable, DataTableColumn } from '@/components/admin/data-table';
import { CrudDeleteDialog } from '@/components/admin/delete-dialog';
import { CrudFormDialog, CrudFormField, useCrudFormValues } from '@/components/admin/form-dialog';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { Badge } from '@/components/ui/badge';
import { RoleInput } from '@/apis/role.api';
import { adminRoles } from '@/hooks/tankstack/admin';
import { useCrudPage } from '@/hooks/tankstack/admin-crud';
import { Role } from '@/shared/types/api.types';
import { z } from 'zod';

type RoleForm = Record<string, unknown>;

const FIELDS: CrudFormField[] = [
  { name: 'code', label: 'Mã vai trò', placeholder: 'vd. ADMIN' },
  { name: 'name', label: 'Tên vai trò', placeholder: 'vd. Quản trị viên' },
  { name: 'description', label: 'Mô tả', type: 'textarea', placeholder: 'Mô tả ngắn (tùy chọn)' },
];

const schema = z.object({
  code: z.string().min(1, 'Mã vai trò là bắt buộc'),
  name: z.string().min(1, 'Tên vai trò là bắt buộc'),
  description: z.string().optional(),
}) as unknown as z.ZodType<RoleForm>;

const COLUMNS: DataTableColumn<Role>[] = [
  {
    key: 'code',
    header: 'Mã',
    render: (role) => <Badge variant="outline" className="font-mono text-xs">{role.code}</Badge>,
  },
  {
    key: 'name',
    header: 'Tên vai trò',
    render: (role) => <span className="font-medium">{role.name}</span>,
  },
  {
    key: 'description',
    header: 'Mô tả',
    render: (role) => role.description ?? <span className="text-muted-foreground">—</span>,
  },
];

/** CRUD Vai trò — backend `GET /api/roles` không phân trang (dùng chung DataTable với envelope giả lập). */
export function RolesClient() {
  const mutations = {
    create: adminRoles.useCreate(),
    update: adminRoles.useUpdate(),
    remove: adminRoles.useDelete(),
  };
  const state = useCrudPage<Role, RoleInput>(mutations);
  const list = adminRoles.useList({ page: state.page, limit: 10, keyword: state.keyword });
  const defaultValues = useCrudFormValues<RoleForm>(FIELDS, state.editing);

  return (
    <div className="flex w-full flex-col gap-4">
      <CrudToolbar
        keyword={state.keywordInput}
        onKeywordChange={state.setKeywordInput}
        searchPlaceholder="Tìm vai trò…"
        onAdd={state.openCreate}
        addLabel="Thêm vai trò"
      />

      {list.isLoading ? (
        <CrudTableSkeleton />
      ) : list.isError ? (
        <ErrorState
          title="Không thể tải danh sách vai trò"
          description="Bạn cần quyền ADMIN/MANAGER để xem danh sách này."
          onRetry={() => list.refetch()}
        />
      ) : (
        <DataTable
          columns={COLUMNS}
          items={list.data?.items ?? []}
          rowKey={(role) => role.id}
          onEdit={state.openEdit}
          onDelete={(role) => state.setDeleteTarget(role)}
          empty={
            <EmptyState title="Không có vai trò nào" description="Thêm vai trò đầu tiên." />
          }
        />
      )}

      <CrudFormDialog
        open={state.dialogOpen}
        onOpenChange={state.setDialogOpen}
        title={state.editing ? 'Sửa vai trò' : 'Thêm vai trò'}
        schema={schema}
        fields={FIELDS}
        defaultValues={defaultValues}
        onSubmit={(values) =>
          state.submit({
            code: String(values.code ?? ''),
            name: String(values.name ?? ''),
            description: values.description ? String(values.description) : undefined,
          })
        }
        submitting={state.saving}
      />

      <CrudDeleteDialog
        target={
          state.deleteTarget ? { id: state.deleteTarget.id, label: state.deleteTarget.name } : null
        }
        onCancel={() => state.setDeleteTarget(null)}
        onConfirm={state.confirmDelete}
        isPending={state.deleting}
        entityLabel="vai trò"
      />
    </div>
  );
}
