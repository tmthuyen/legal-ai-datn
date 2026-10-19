import { ApiPaginatedResponse, ApiResponse, User } from '@/shared/types/api.types';
import axiosClient from '../lib/axiosClient';

export const userApi = {
  getSessions: () => axiosClient.get('/users/me/sessions'),
  updateProfile: async (data: any): Promise<ApiResponse<User>> => {
    const { data: userData } = await axiosClient.put('/users/me', data);
    return userData;
  },
  uploadAvatar: (formData: FormData) =>
    axiosClient.post('/users/me/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Admin
  /** Danh sách user (ADMIN) — `{page, limit, keyword}` (keyword ILIKE fullName/email). */
  getAllUsers: async (params: {
    page?: number;
    limit?: number;
    keyword?: string;
  }): Promise<ApiPaginatedResponse<User[]>> => {
    const { data } = await axiosClient.get('/users', { params });
    return data;
  },
  getUserById: async (id: number | string): Promise<ApiResponse<User>> => {
    const { data } = await axiosClient.get(`/users/${id}`);
    return data;
  },
  createUser: async (data: any): Promise<ApiResponse<User>> => {
    const { data: userData } = await axiosClient.post('/users', data);

    return userData;
  },
  updateUserAdmin: async (id: number | string, data: any): Promise<ApiResponse<User>> => {
    const { data: userData } = await axiosClient.put(`/users/${id}`, data);
    return userData;
  },
  /** Gán vai trò cho user (ADMIN) — `PATCH /users/:id/roles` `{roleIds}`. */
  updateUserRoles: async (
    id: number | string,
    roleIds: Array<number | string>,
  ): Promise<ApiResponse<User>> => {
    const { data } = await axiosClient.patch(`/users/${id}/roles`, { roleIds });
    return data;
  },
  deleteUser: async (id: number | string): Promise<ApiResponse<null>> => {
    const { data } = await axiosClient.delete(`/users/${id}`);
    return data;
  },

  // avatar
  updateUserAvatar: async (formData: FormData): Promise<ApiResponse<string>> => {
    const { data: userData } = await axiosClient.post(`/users/avatar`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return userData;
  },
};
