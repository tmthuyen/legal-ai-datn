'use client';

import { ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { EmptyState } from '@/components/common/EmptyState';
import { SectionHeader } from '@/components/common/SectionHeader';
import { Skeleton } from '@/components/ui/skeleton';
import { MovieGrid, MovieGridSkeleton } from '@/components/movie/movie-grid';
import useGenre from '@/hooks/tankstack/useGenre';
import useMovie from '@/hooks/tankstack/useMovie';

export function LatestMovies() {
  const { data, isLoading } = useMovie.useGetMovies({ page: 1, limit: 12 });
  const { data: genres, isLoading: isGenresLoading } = useGenre.useGetAll({ limit: 20 });

  return (
    <div className="w-full space-y-10">
      <section className="space-y-4">
        <SectionHeader
          title="Phim mới nhất"
          description="Những bộ phim vừa được thêm vào hệ thống."
          action={
            <Link
              href="/movies"
              className="text-primary inline-flex shrink-0 items-center gap-1 text-sm font-medium hover:underline"
            >
              Xem tất cả <ArrowRight className="size-4" />
            </Link>
          }
        />

        {isLoading ? (
          <MovieGridSkeleton items={12} />
        ) : data && data.movies.length > 0 ? (
          <MovieGrid movies={data.movies} />
        ) : (
          <EmptyState title="Chưa có phim nào" description="Hệ thống chưa có phim để hiển thị." />
        )}
      </section>

      <section className="space-y-4">
        <SectionHeader title="Khám phá theo thể loại" />
        {isGenresLoading ? (
          <div className="flex flex-wrap gap-2">
            {Array.from({ length: 8 }).map((_, index) => (
              <Skeleton key={index} className="h-9 w-24 rounded-full" />
            ))}
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {genres?.map((genre) => (
              <Link
                key={genre.id}
                href={`/movies?genre=${genre.id}`}
                className="bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded-full border px-4 py-2 text-sm font-medium transition-colors"
              >
                {genre.name}
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
