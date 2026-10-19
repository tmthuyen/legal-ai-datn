import { ApiPaginatedResponse, ApiResponse } from '@/shared/types/api.types';
import { People } from '@/shared/types/movie.types';
import axiosClient from '../lib/axiosClient';

export interface PeopleQuery {
  page?: number;
  limit?: number;
  keyword?: string;
}

/** Input tạo/cập nhật people — khớp `CreatePeopleDto` của backend. */
export interface PeopleInput {
  fullName: string;
  birthDate?: string;
  nationality?: string;
  gender?: string;
  mainRole?: string;
}

export const peopleApi = {
  /** Danh sách diễn viên/đạo diễn (public). */
  getAll: async (params: PeopleQuery = {}): Promise<ApiPaginatedResponse<People[]>> => {
    const { data } = await axiosClient.get('/peoples', { params });
    return data;
  },
  /** Chi tiết theo id (public). */
  getById: async (id: number | string): Promise<ApiResponse<People>> => {
    const { data } = await axiosClient.get(`/peoples/${id}`);
    return data;
  },
  /** Tạo mới (ADMIN). */
  create: async (input: PeopleInput): Promise<ApiResponse<People>> => {
    const { data } = await axiosClient.post('/peoples', input);
    return data;
  },
  /** Cập nhật (ADMIN) — backend nhận `PATCH`. */
  update: async (id: number | string, input: Partial<PeopleInput>): Promise<ApiResponse<People>> => {
    const { data } = await axiosClient.patch(`/peoples/${id}`, input);
    return data;
  },
  /** Xóa (ADMIN). */
  remove: async (id: number | string): Promise<ApiResponse<null>> => {
    const { data } = await axiosClient.delete(`/peoples/${id}`);
    return data;
  },
};
