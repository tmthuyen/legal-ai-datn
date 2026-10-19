import { ApiPaginatedResponse, ApiResponse } from '@/shared/types/api.types';
import { Movie, MovieDetail, MovieQuery } from '@/shared/types/movie.types';
import axiosClient from '../lib/axiosClient';

/**
 * Input tạo/cập nhật phim — khớp `CreateMovieDto` của backend
 * (`UpdateMovieDto` = Partial). Id dạng string ở client (bigint).
 */
export interface MovieAdminInput {
  title: string;
  titleVi?: string;
  overview?: string;
  overviewVi?: string;
  releaseDate?: string;
  posterPath?: string;
  backdropPath?: string;
  originCountry?: string;
  originalLanguage?: string;
  budget?: number;
  revenue?: number;
  status?: string;
  video?: boolean;
  genreIds?: number[];
  countryId?: number;
  peopleIds?: number[];
}

export const movieApi = {
  /** Danh sách phim (public) — chỉ nhận `page`/`limit`/`keyword`. */
  getAll: async (params: MovieQuery = {}): Promise<ApiPaginatedResponse<Movie[]>> => {
    const { data } = await axiosClient.get('/movies', { params });
    return data;
  },
  /** Chi tiết phim theo id (public). */
  getById: async (id: number | string): Promise<ApiResponse<MovieDetail>> => {
    const { data } = await axiosClient.get(`/movies/${id}`);
    return data;
  },
  /** Tăng lượt xem cho phim (public, optional auth). */
  incrementView: async (id: number | string): Promise<ApiResponse<{ viewCount: number }>> => {
    const { data } = await axiosClient.post(`/movies/${id}/view`);
    return data;
  },
  /** Tạo phim (ADMIN). */
  create: async (input: MovieAdminInput): Promise<ApiResponse<Movie>> => {
    const { data } = await axiosClient.post('/movies', input);
    return data;
  },
  /** Cập nhật phim (ADMIN) — backend nhận `PATCH`. */
  update: async (id: number | string, input: Partial<MovieAdminInput>): Promise<ApiResponse<Movie>> => {
    const { data } = await axiosClient.patch(`/movies/${id}`, input);
    return data;
  },
  /** Xóa phim (ADMIN). */
  remove: async (id: number | string): Promise<ApiResponse<null>> => {
    const { data } = await axiosClient.delete(`/movies/${id}`);
    return data;
  },
};
