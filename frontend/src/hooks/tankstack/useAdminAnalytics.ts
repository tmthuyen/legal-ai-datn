import { legalAdminApi } from '@/apis/legal.api';
import { parseAxiosError } from '@/lib/axiosClient';
import { AdminAnalytics, LegalUser } from '@/shared/types/legal.types';
import { Pagination } from '@/shared/types/api.types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

/** QueryKey gốc của domain quản trị user. */
export const ADMIN_USERS_QUERY_KEY = 'admin-users';

/** Kết quả danh sách user phân trang cho bảng admin. */
export interface AdminUsersListResult {
  items: LegalUser[];
  pagination: Pagination;
}

/** Danh sách người dùng (`GET /admin/users`) — hỗ trợ phân trang + tìm theo email/username. */
export function useAdminUsers(params: {
  page?: number;
  limit?: number;
  search?: string;
  enabled?: boolean;
}) {
  const { page = 1, limit = 10, search = '', enabled = true } = params;
  return useQuery({
    queryKey: [ADMIN_USERS_QUERY_KEY, page, limit, search],
    queryFn: async (): Promise<AdminUsersListResult> => {
      const response = await legalAdminApi.getUsers({
        page,
        limit,
        search: search || undefined,
      });
      return { items: response.result ?? [], pagination: response.pagination };
    },
    enabled,
    staleTime: 1000 * 30,
    placeholderData: (previous) => previous,
  });
}

/** Khóa/mở khóa tài khoản (`PUT /admin/users/:id/status`). */
export function useUpdateUserStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      legalAdminApi.updateUserStatus(id, { isActive }),
    onSuccess: (response) => {
      toast.success(response.message || 'Đã cập nhật trạng thái tài khoản.');
      queryClient.invalidateQueries({ queryKey: [ADMIN_USERS_QUERY_KEY] });
    },
    onError: (error) =>
      toast.error(parseAxiosError(error).message || 'Không thể cập nhật trạng thái tài khoản.'),
  });
}

/** Thống kê tổng quan (`GET /admin/analytics`). */
export function useAdminAnalytics() {
  return useQuery({
    queryKey: ['admin-analytics'],
    queryFn: async (): Promise<AdminAnalytics> => {
      const response = await legalAdminApi.getAnalytics();
      return response.result;
    },
    staleTime: 1000 * 60,
  });
}
