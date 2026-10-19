'use client';

import { useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { CrudFormDialog, CrudFormField } from '@/components/admin/form-dialog';
import { userApi } from '@/apis/user.api';
import { adminRoles } from '@/hooks/tankstack/admin';
import { parseAxiosError } from '@/lib/axiosClient';
import { User } from '@/shared/types/api.types';
import { z } from 'zod';

type RoleForm = Record<string, unknown>;

const schema = z.object({ roleIds: z.array(z.string()) }) as unknown as z.ZodType<RoleForm>;

interface AssignRolesDialogProps {
  /** User đang phân quyền — `null` = đóng dialog. */
  user: User | null;
  onCancel: () => void;
}

/**
 * Dialog phân quyền (gán vai trò) cho user — tái sử dụng `CrudFormDialog`
 * với 1 field multiselect; gọi `PATCH /users/:id/roles`.
 */
export function AssignRolesDialog({ user, onCancel }: AssignRolesDialogProps) {
  const queryClient = useQueryClient();
  const roles = adminRoles.useList({ page: 1, limit: 100, enabled: Boolean(user) });

  const fields = useMemo<CrudFormField[]>(
    () => [
      {
        name: 'roleIds',
        label: 'Vai trò',
        type: 'multiselect',
        options: (roles.data?.items ?? []).map((role) => ({
          value: String(role.id),
          label: `${role.name} (${role.code})`,
        })),
      },
    ],
    [roles.data],
  );

  const defaultValues = useMemo<RoleForm>(
    () => ({ roleIds: (user?.roles ?? []).map((role) => String(role.id)) }),
    [user],
  );

  const save = useMutation({
    mutationFn: async (roleIds: string[]) => {
      if (!user) return;
      // Backend `PATCH /users/:id/roles` nhận `{roleIds: number[]}` (docs/BACKEND.md).
      await userApi.updateUserRoles(
        user.id,
        roleIds.map((roleId) => Number(roleId)).filter((roleId) => !Number.isNaN(roleId)),
      );
    },
    onSuccess: () => {
      toast.success('Đã cập nhật vai trò.');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      onCancel();
    },
    onError: (error) =>
      toast.error(parseAxiosError(error).message || 'Không thể cập nhật vai trò.'),
  });

  return (
    <CrudFormDialog
      open={Boolean(user)}
      onOpenChange={(open) => {
        if (!open) onCancel();
      }}
      title={`Phân quyền — ${user?.fullName ?? user?.email ?? ''}`}
      description="Chọn các vai trò áp dụng cho người dùng này."
      schema={schema}
      fields={fields}
      defaultValues={defaultValues}
      onSubmit={(values) =>
        save.mutateAsync(Array.isArray(values.roleIds) ? (values.roleIds as string[]) : []).catch(
          () => undefined,
        )
      }
      submitting={save.isPending}
    />
  );
}
