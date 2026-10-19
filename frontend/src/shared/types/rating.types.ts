import { Movie } from './movie.types';

/**
 * Đánh giá sao — `POST /api/ratings`, `GET /api/ratings/movie/:movieId`.
 * Unique theo (user, movie) — user chỉ đánh giá 1 lần/phim (submit lại sẽ lỗi
 * unique từ server).
 */
export interface Rating {
  id: number;
  /** Điểm 0–5. */
  rating: number;
  user?: { id: string; fullName?: string; email?: string; avatarUrl?: string };
  movie?: Movie;
  createdAt?: string;
  createdBy?: string;
  updatedAt?: string;
  updatedBy?: string;
}

/** Stats phim đi kèm WS event `movie-{id}-rating`. */
export interface MovieStats {
  voteCount: number;
  voteAverage: number;
}
