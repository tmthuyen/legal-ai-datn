import { ApiPaginatedResponse, ApiResponse } from '@/shared/types/api.types';
import { Country } from '@/shared/types/movie.types';
import axiosClient from '../lib/axiosClient';

export interface CountryQuery {
  page?: number;
  limit?: number;
  keyword?: string;
}

export const countryApi = {
  /** Danh sách quốc gia (public). */
  getAll: async (params: CountryQuery = {}): Promise<ApiPaginatedResponse<Country[]>> => {
    const { data } = await axiosClient.get('/countries', { params });
    return data;
  },
  /** Chi tiết quốc gia theo id (public). */
  getById: async (id: number | string): Promise<ApiResponse<Country>> => {
    const { data } = await axiosClient.get(`/countries/${id}`);
    return data;
  },
  /** Tạo mới (ADMIN). */
  create: async (input: { name: string; code: string }): Promise<ApiResponse<Country>> => {
    const { data } = await axiosClient.post('/countries', input);
    return data;
  },
  /** Cập nhật (ADMIN) — backend nhận `PATCH`. */
  update: async (
    id: number | string,
    input: Partial<{ name: string; code: string }>,
  ): Promise<ApiResponse<Country>> => {
    const { data } = await axiosClient.patch(`/countries/${id}`, input);
    return data;
  },
  /** Xóa (ADMIN). */
  remove: async (id: number | string): Promise<ApiResponse<null>> => {
    const { data } = await axiosClient.delete(`/countries/${id}`);
    return data;
  },
};
