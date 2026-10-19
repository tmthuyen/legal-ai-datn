'use client';

import { ArrowLeft, Film } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useRef } from 'react';
import { ErrorState } from '@/components/common/ErrorState';
import { Skeleton } from '@/components/ui/skeleton';
import useMovie from '@/hooks/tankstack/useMovie';
import { MovieActions } from './movie-actions';
import { MovieComments } from './movie-comments';
import { MovieDetail } from './movie-detail';
import { MovieRating } from './movie-rating';
import { SimilarMovies } from './similar-movies';

function DetailSkeleton() {
  return (
    <div className="space-y-6" aria-hidden="true">
      <div className="grid gap-6 rounded-2xl border bg-card p-6 md:grid-cols-[280px_1fr] md:p-8">
        <Skeleton className="aspect-[2/3] w-full rounded-xl" />
        <div className="space-y-4">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
          <div className="flex gap-2">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-6 w-24 rounded-full" />
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="size-11 rounded-full" />
            <Skeleton className="size-11 rounded-full" />
            <Skeleton className="size-11 rounded-full" />
          </div>
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-4/6" />
        </div>
      </div>
      <Skeleton className="h-24 w-full rounded-xl" />
      <Skeleton className="h-64 w-full rounded-xl" />
    </div>
  );
}

/**
 * Container trang chi tiết phim (client): fetch `GET /api/movies/:id`,
 * tăng view 1 lần khi mount (`POST /api/movies/:id/view` — đồng bộ `viewCount`
 * vào cache ngay khi server trả về), render các khối thông tin / đánh giá /
 * bình luận / phim tương tự.
 */
export function MovieDetailView({ id }: { id: string }) {
  const { data: movie, isLoading, isError, refetch } = useMovie.useGetMovieDetail(id);
  const incrementView = useMovie.useIncrementView();

  // Chỉ tăng view đúng 1 lần cho mỗi id (StrictMode dev mount 2 lần → ref guard)
  const viewedIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!id || viewedIdRef.current === id) return;
    viewedIdRef.current = id;
    incrementView.mutate(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (isLoading) {
    return (
      <div className="animate-fade-in w-full space-y-6 pb-10">
        <DetailSkeleton />
      </div>
    );
  }

  if (isError || !movie) {
    return (
      <div className="animate-fade-in w-full space-y-6 pb-10">
        <ErrorState
          title="Không tìm thấy phim"
          description="Phim không tồn tại hoặc đã bị gỡ xuống. Vui lòng thử lại."
          onRetry={() => refetch()}
          action={
            <Link
              href="/movies"
              className="text-primary inline-flex items-center gap-1 text-sm font-medium hover:underline"
            >
              <ArrowLeft className="size-4" aria-hidden="true" />
              Quay lại danh sách phim
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="animate-fade-in w-full space-y-8 pb-10">
      <nav aria-label="Điều hướng" className="flex items-center gap-2 text-sm">
        <Link
          href="/movies"
          className="text-muted-foreground hover:text-foreground inline-flex items-center gap-1 transition-colors"
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          Danh sách phim
        </Link>
        <span className="text-muted-foreground" aria-hidden="true">
          /
        </span>
        <span className="inline-flex min-w-0 items-center gap-1 truncate font-medium">
          <Film className="size-4 shrink-0" aria-hidden="true" />
          <span className="truncate">{movie.titleVi || movie.title || 'Chi tiết phim'}</span>
        </span>
      </nav>

      <MovieDetail movie={movie} />

      {/* Tương tác nhanh: thích / không thích / yêu thích / muốn xem (variant detail) */}
      <div className="flex flex-wrap items-center gap-4">
        <MovieActions movieId={movie.id} variant="detail" />
        <p className="text-muted-foreground text-sm">
          Thích hoặc không thích phim này, thêm vào danh sách của bạn.
        </p>
      </div>

      <MovieRating movie={movie} />

      <SimilarMovies genres={movie.genres} />

      <MovieComments movieId={movie.id} />
    </div>
  );
}
