import { BaseDto } from './api.types';
import { Movie } from './movie.types';

/**
 * Kiểu tương tác — khớp enum `InteractionType` của backend
 * (`like`, `dislike`, `favorite`, `watchlist`, `rating`, `comment`, `click`).
 */
export type InteractionType =
  | 'like'
  | 'dislike'
  | 'favorite'
  | 'watchlist'
  | 'rating'
  | 'comment'
  | 'click';

/**
 * Tương tác — `GET /api/interactions*`.
 *
 * Lưu ý: `movieId`/`user` chỉ có ở các endpoint join `movie`/`user`
 * (`my-history`, `my-favorites`).
 */
export interface Interaction extends BaseDto {
  id: number;
  score: number;
  type: InteractionType;
  user?: { id: string; fullName?: string; email?: string; avatarUrl?: string };
  movie?: Movie;
  movieId?: number | string;
}

/**
 * Kết quả `POST /api/interactions` — **TOGGLE**: gọi 1 lần để bật,
 * gọi lại để tắt → đọc `action` (`added`/`removed`).
 */
export interface ToggleInteractionResult {
  success: boolean;
  action: 'added' | 'removed';
  type: InteractionType;
  data?: Interaction;
}
