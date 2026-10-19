import { ApiPaginatedResponse, ApiResponse, Genre } from '@/shared/types/api.types';
import axiosClient from '../lib/axiosClient';

export interface GenreQuery {
  page?: number;
  limit?: number;
  keyword?: string;
}

export const genreApi = {
  getAll: async (params: GenreQuery = {}): Promise<ApiPaginatedResponse<Genre[]>> => {
    const { data } = await axiosClient.get('/genres', { params });
    return data;
  },
  getById: async (id: string): Promise<ApiResponse<Genre>> => {
    const { data } = await axiosClient.get(`/genres/${id}`);
    return data;
  },
  create: async (genre: Partial<Genre>): Promise<ApiResponse<Genre>> => {
    const { data } = await axiosClient.post('/genres', genre);
    return data;
  },
  /** Cập nhật (ADMIN) — backend nhận `PATCH` (khớp `genres.controller.ts`). */
  update: async (id: string, genre: Partial<Genre>): Promise<ApiResponse<Genre>> => {
    const { data } = await axiosClient.patch(`/genres/${id}`, genre);
    return data;
  },
  delete: async (id: string): Promise<ApiResponse<null>> => {
    const { data } = await axiosClient.delete(`/genres/${id}`);
    return data;
  },
};
