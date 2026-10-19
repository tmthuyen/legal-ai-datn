'use client';

import { Eye, Film, Star } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { MovieActions } from './movie-actions';
import { Movie } from '@/shared/types/movie.types';
import { getMovieTitle, getPosterUrl, getReleaseYear } from '@/shared/utils/movie';

interface MovieCardProps {
  movie: Movie;
  /** Ẩn bộ nút tương tác (dùng cho các card không cần actions). */
  hideActions?: boolean;
}

/**
 * Card phim dùng chung (danh sách `/movies`, trang chủ…).
 *
 * - Click toàn card → `/movies/[id]` (stretched link, `z-10`).
 * - Hover / focus (bàn phím) → overlay hiện thêm thông tin (thể loại, mô tả,
 *   năm, lượt xem). Thiết bị touch (`hover: none`) không dựa vào hover.
 * - Nút tương tác (thích/yêu thích/muốn xem) nằm trên overlay, `z-20`,
 *   chặn click xuyên xuống stretched link.
 */
export function MovieCard({ movie, hideActions = false }: MovieCardProps) {
  const poster = getPosterUrl(movie.posterPath || movie.backdropPath);
  const title = getMovieTitle(movie);
  const year = getReleaseYear(movie.releaseDate);
  const rating = typeof movie.voteAverage === 'number' ? movie.voteAverage : 0;
  const views = Number(movie.viewCount) || 0;
  const overview = movie.overviewVi || movie.overview || '';
  const genres = (movie.genres ?? []).slice(0, 3);

  return (
    <article className="group bg-card text-card-foreground focus-within:ring-ring relative flex flex-col overflow-hidden rounded-lg border shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg focus-within:ring-2">
      <div className="bg-muted relative aspect-[2/3] w-full overflow-hidden">
        {poster ? (
          <Image
            src={poster}
            alt={title}
            fill
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 25vw, 16vw"
            className="object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="text-muted-foreground flex h-full w-full items-center justify-center">
            <Film className="size-10" />
          </div>
        )}

        {rating > 0 && (
          <span className="bg-background/85 text-foreground absolute top-2 right-2 z-20 inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold shadow-sm backdrop-blur">
            <Star className="size-3 fill-current text-yellow-500" aria-hidden="true" />
            {rating.toFixed(1)}
          </span>
        )}

        {/* Overlay thông tin khi hover/focus — ẩn trên thiết bị không có hover */}
        <div
          aria-hidden="true"
          className="from-background/95 via-background/75 absolute inset-0 z-10 flex flex-col justify-end gap-1.5 bg-gradient-to-t to-transparent p-3 opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 [@media(hover:none)]:hidden"
        >
          {genres.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {genres.map((genre) => (
                <span
                  key={genre.id}
                  className="bg-secondary text-secondary-foreground rounded-full px-2 py-0.5 text-[11px] font-medium"
                >
                  {genre.name}
                </span>
              ))}
            </div>
          )}
          {overview && (
            <p className="text-muted-foreground line-clamp-3 text-xs leading-relaxed">
              {overview}
            </p>
          )}
          <div className="text-muted-foreground flex items-center gap-3 text-xs">
            {year && <span>{year}</span>}
            <span className="inline-flex items-center gap-1">
              <Eye className="size-3" aria-hidden="true" />
              {views.toLocaleString('vi-VN')} lượt xem
            </span>
          </div>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-2 p-3">
        {/* Title max 2 dòng, reserved min-h 2 dòng → card không nhảy size khi tên phim ngắn/dài */}
        <h3 className="line-clamp-2 min-h-[2.5rem] text-sm leading-snug font-semibold">{title}</h3>
        <div className="mt-auto flex items-center justify-between gap-2">
          <p className="text-muted-foreground text-xs">{year || 'Đang cập nhật'}</p>
          {!hideActions && <MovieActions movieId={movie.id} variant="card" />}
        </div>
      </div>

      {/* Stretched link: click toàn card → chi tiết phim */}
      <Link
        href={`/movies/${movie.id}`}
        title={title}
        aria-label={title}
        className="focus-visible:ring-ring absolute inset-0 z-10 rounded-lg focus-visible:ring-2 focus-visible:outline-none"
      />
    </article>
  );
}
