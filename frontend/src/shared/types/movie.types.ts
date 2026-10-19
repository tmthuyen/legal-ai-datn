import { BaseDto, Genre } from './api.types';

/** Quốc gia — `GET /api/countries` */
export interface Country extends BaseDto {
  id: number;
  name: string;
  code: string;
}

/** Người tham gia phim (diễn viên/đạo diễn) */
export interface People extends BaseDto {
  id: number;
  /** Khớp entity backend (`fullName`) — `name` là legacy type cũ. */
  fullName?: string;
  name?: string;
  birthDate?: string;
  nationality?: string;
  gender?: string;
  mainRole?: string;
  profilePath?: string;
}

export interface MoviePeople extends BaseDto {
  id?: number;
  role?: string;
  job?: string;
  character?: string;
  people?: People;
}

/**
 * Phim — `GET /api/movies`, `GET /api/movies/:id`.
 *
 * Lưu ý: các cột `bigint` (`id`, `viewCount`, `voteCount`…) có thể được
 * serialize thành string ở runtime, nên khi dùng nên ép `Number(...)`
 * hoặc `String(...)` tùy ngữ cảnh.
 */
export interface Movie extends BaseDto {
  id: number;
  tmdbId?: number;
  imdbId?: string;
  title?: string;
  titleVi?: string;
  overview?: string;
  overviewVi?: string;
  releaseDate?: string;
  posterPath?: string;
  backdropPath?: string;
  voteAverage?: number;
  voteCount?: number;
  viewCount?: number;
  genres?: Genre[];
  country?: Country;
}

export interface MovieDetail extends Movie {
  moviePeoples?: MoviePeople[];
}

/** Query hợp lệ của `GET /api/movies` — backend chỉ nhận `page`/`limit`/`keyword`. */
export interface MovieQuery {
  page?: number;
  limit?: number;
  keyword?: string;
}

/** Kết quả danh sách phim = `result` + `pagination` của envelope. */
export interface MovieListResult {
  movies: Movie[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}
