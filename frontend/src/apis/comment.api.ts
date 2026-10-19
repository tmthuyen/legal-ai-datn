import { ApiPaginatedResponse, ApiResponse } from '@/shared/types/api.types';
import { Comment } from '@/shared/types/comment.types';
import axiosClient from '../lib/axiosClient';

export const commentApi = {
  /** Thêm bình luận (JWT) — body `{ content, movieId, parentId? }`. */
  create: async (input: {
    content: string;
    movieId: number | string;
    parentId?: number | string;
  }): Promise<ApiResponse<Comment>> => {
    const { data } = await axiosClient.post('/comments', input);
    return data;
  },
  /**
   * Bình luận của một phim (public) — không truyền `parentId` → root;
   * truyền `parentId` → các reply trực tiếp của comment đó.
   */
  getByMovie: async (
    movieId: number | string,
    params: { page?: number; limit?: number; parentId?: number | string } = {},
  ): Promise<ApiPaginatedResponse<Comment[]>> => {
    const { page, limit, parentId } = params;
    const { data } = await axiosClient.get(`/comments/movie/${movieId}`, {
      params: { page, limit, parentId },
    });
    return data;
  },
  /** Toàn bộ bình luận (public, admin) — `{page, limit}`, join `user` + `movie`. */
  getAll: async (params: {
    page?: number;
    limit?: number;
  }): Promise<ApiPaginatedResponse<Comment[]>> => {
    const { data } = await axiosClient.get('/comments', { params });
    return data;
  },
  /** Xóa bình luận (ADMIN). */
  remove: async (id: number | string): Promise<ApiResponse<null>> => {
    const { data } = await axiosClient.delete(`/comments/${id}`);
    return data;
  },
};
