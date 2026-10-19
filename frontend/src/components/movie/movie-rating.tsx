'use client';

import { Star } from 'lucide-react';
import { useState } from 'react';
import useRating from '@/hooks/tankstack/useRating';
import { useRequireLogin } from '@/hooks/useRequireLogin';
import { useMovieSocket } from '@/hooks/useMovieSocket';
import { cn } from '@/lib/utils';

interface MovieRatingProps {
  /** Phim đang hiển thị. */
  movie: {
    id: number | string;
    voteAverage?: number;
    voteCount?: number;
  };
}

/**
 * Widget đánh giá sao trên trang chi tiết:
 * - Hiển thị `voteAverage`/`voteCount` hiện tại (cập nhật realtime qua WS
 *   `movie-{id}-rating` → `payload.movieStats`).
 * - Nút 1–5 sao (aria-label rõ ràng) → `POST /api/ratings` (JWT);
 *   chưa đăng nhập → hiện hộp thoại yêu cầu đăng nhập (`useRequireLogin`).
 */
export function MovieRating({ movie }: MovieRatingProps) {
  const requireLogin = useRequireLogin();

  const [stats, setStats] = useState({
    voteAverage: typeof movie.voteAverage === 'number' ? movie.voteAverage : 0,
    voteCount: Number(movie.voteCount) || 0,
  });
  const [hoverStar, setHoverStar] = useState(0);

  const createRating = useRating.useCreateRating(movie.id);

  // Realtime: cập nhật voteAverage/voteCount khi user khác đánh giá
  useMovieSocket({
    movieId: movie.id,
    onRating: (payload) => {
      const next = payload?.movieStats;
      if (next) {
        setStats({
          voteAverage: Number(next.voteAverage) || 0,
          voteCount: Number(next.voteCount) || 0,
        });
      }
    },
  });

  const handleRate = (value: number) => {
    if (!requireLogin()) return;
    createRating.mutate(value);
  };

  const displayStar = hoverStar || Math.round(stats.voteAverage);

  return (
    <section
      aria-label="Đánh giá phim"
      className="bg-card flex flex-wrap items-center justify-between gap-4 rounded-xl border p-4"
    >
      <div className="flex items-baseline gap-3">
        <span className="text-3xl font-extrabold tabular-nums">{stats.voteAverage.toFixed(1)}</span>
        <div className="text-muted-foreground text-sm">
          <div className="text-foreground mb-0.5 flex items-center gap-0.5" aria-hidden="true">
            {Array.from({ length: 5 }).map((_, index) => (
              <Star
                key={index}
                className={cn(
                  'size-4',
                  index < displayStar ? 'fill-yellow-400 text-yellow-400' : 'text-muted-foreground/40 fill-muted-foreground/20',
                )}
              />
            ))}
          </div>
          <span>{stats.voteCount.toLocaleString('vi-VN')} lượt đánh giá</span>
        </div>
      </div>

      <div className="flex items-center gap-1.5">
        <span className="text-muted-foreground mr-1 text-sm">Đánh giá của bạn:</span>
        {Array.from({ length: 5 }).map((_, index) => {
          const value = index + 1;
          return (
            <button
              key={value}
              type="button"
              disabled={createRating.isPending}
              aria-label={`Đánh giá ${value} trên 5 sao`}
              onClick={() => handleRate(value)}
              onMouseEnter={() => setHoverStar(value)}
              onMouseLeave={() => setHoverStar(0)}
              onFocus={() => setHoverStar(value)}
              onBlur={() => setHoverStar(0)}
              className={cn(
                'rounded p-1.5 transition-all hover:bg-accent focus-visible:ring-ring cursor-pointer focus-visible:ring-2 focus-visible:outline-none active:scale-90 disabled:cursor-not-allowed disabled:opacity-50',
                value <= displayStar
                  ? 'text-yellow-500'
                  : 'text-muted-foreground hover:text-muted-foreground/80',
              )}
            >
              <Star className="size-6" />
            </button>
          );
        })}
      </div>
    </section>
  );
}
