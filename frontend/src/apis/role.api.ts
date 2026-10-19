import { ApiResponse, Role } from '@/shared/types/api.types';
import axiosClient from '../lib/axiosClient';

/** Input tạo role — khớp `CreateRoleDto`; `UpdateRoleDto` = Partial. */
export interface RoleInput {
  code: string;
  name: string;
  description?: string;
}

export const roleApi = {
  /** Danh sách vai trò (ADMIN/MANAGER) — backend không nhận phân trang. */
  getAll: async (): Promise<ApiResponse<Role[]>> => {
    const { data } = await axiosClient.get('/roles');
    return data;
  },
  /** Tạo vai trò (JWT). */
  create: async (input: RoleInput): Promise<ApiResponse<Role>> => {
    const { data } = await axiosClient.post('/roles', input);
    return data;
  },
  /** Cập nhật vai trò (JWT) — backend nhận `PATCH`. */
  update: async (id: number | string, input: Partial<RoleInput>): Promise<ApiResponse<Role>> => {
    const { data } = await axiosClient.patch(`/roles/${id}`, input);
    return data;
  },
  /** Xóa vai trò (JWT). */
  remove: async (id: number | string): Promise<ApiResponse<null>> => {
    const { data } = await axiosClient.delete(`/roles/${id}`);
    return data;
  },
};
