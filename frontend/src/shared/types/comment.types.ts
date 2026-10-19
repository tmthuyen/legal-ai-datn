import { Movie } from './movie.types';

/**
 * Bình luận phân cấp — `POST /api/comments`, `GET /api/comments/movie/:movieId`.
 * `parentId` null/0 = root; list root có thêm `replyCount` (số reply trực tiếp).
 */
export interface Comment {
  id: number;
  content: string;
  /** `null`/`0`/không có = bình luận gốc. */
  parentId?: number | string | null;
  user?: { id: string; fullName?: string; email?: string; avatarUrl?: string };
  movie?: Movie;
  /** Số reply trực tiếp (chỉ có ở danh sách root). */
  replyCount?: number;
  createdAt?: string;
  createdBy?: string;
  updatedAt?: string;
  updatedBy?: string;
}
