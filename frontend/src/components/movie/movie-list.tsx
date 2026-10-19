'use client';

import { Clapperboard } from 'lucide-react';
import { useEffect, useMemo, useRef } from 'react';
import { DataPagination } from '@/components/common/DataPagination';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import useMovie from '@/hooks/tankstack/useMovie';
import { useMovieFilterStore } from '@/stores/movie-filter.store';
import { MovieFilters } from './movie-filters';
import { MovieGrid, MovieGridSkeleton } from './movie-grid';

interface MovieListProps {
  initialGenreId?: string;
  initialCountryId?: string;
  initialKeyword?: string;
}

export function MovieList({ initialGenreId, initialCountryId, initialKeyword }: MovieListProps) {
  const keyword = useMovieFilterStore((state) => state.keyword);
  const genreId = useMovieFilterStore((state) => state.genreId);
  const countryId = useMovieFilterStore((state) => state.countryId);
  const sort = useMovieFilterStore((state) => state.sort);
  const page = useMovieFilterStore((state) => state.page);
  const limit = useMovieFilterStore((state) => state.limit);
  const setPage = useMovieFilterStore((state) => state.setPage);
  const setFilter = useMovieFilterStore((state) => state.setFilter);

  // Seed bộ lọc từ URL (ví dụ `/movies?genre=28&keyword=avengers`).
  // Seed lại khi URL đổi (vd. submit tìm kiếm từ header ngay trên trang /movies) —
  // không chỉ khi mount, vì cùng route không remount.
  const isSeeded = useRef(false);
  const lastSeed = useRef({
    genre: initialGenreId,
    country: initialCountryId,
    keyword: initialKeyword,
  });
  useEffect(() => {
    const changed =
      lastSeed.current.genre !== initialGenreId ||
      lastSeed.current.country !== initialCountryId ||
      lastSeed.current.keyword !== initialKeyword;

    if (!isSeeded.current) {
      isSeeded.current = true;
    } else if (!changed) {
      return;
    }
    lastSeed.current = {
      genre: initialGenreId,
      country: initialCountryId,
      keyword: initialKeyword,
    };

    const initial: { genreId?: string; countryId?: string; keyword?: string } = {};
    if (initialGenreId) initial.genreId = initialGenreId;
    if (initialCountryId) initial.countryId = initialCountryId;
    if (initialKeyword) initial.keyword = initialKeyword;
    if (Object.keys(initial).length > 0) {
      setFilter(initial);
    }
  }, [initialGenreId, initialCountryId, initialKeyword, setFilter]);

  const { data, isLoading, isError, isFetching, refetch } = useMovie.useGetMovies({
    page,
    limit,
    keyword,
  });

  const movies = data?.movies ?? [];

  // Lọc/sắp xếp client-side vì `GET /api/movies` chỉ hỗ trợ page/limit/keyword.
  const visibleMovies = useMemo(() => {
    let list = [...movies];

    if (genreId) {
      list = list.filter((movie) => movie.genres?.some((genre) => String(genre.id) === genreId));
    }
    if (countryId) {
      list = list.filter((movie) => String(movie.country?.id) === countryId);
    }
    if (sort === 'rating') {
      list = list.sort((a, b) => (b.voteAverage ?? 0) - (a.voteAverage ?? 0));
    } else if (sort === 'popular') {
      list = list.sort((a, b) => (Number(b.viewCount) || 0) - (Number(a.viewCount) || 0));
    }

    return list;
  }, [movies, genreId, countryId, sort]);

  const hasActiveFilter = !!keyword || !!genreId || !!countryId || sort !== 'newest';

  const handlePageChange = (nextPage: number) => {
    setPage(nextPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="flex w-full flex-col gap-6">
      <MovieFilters />

      {isLoading ? (
        <MovieGridSkeleton items={12} />
      ) : isError ? (
        <ErrorState
          title="Không thể tải danh sách phim"
          description="Vui lòng kiểm tra kết nối và thử lại."
          onRetry={() => refetch()}
        />
      ) : visibleMovies.length === 0 ? (
        <EmptyState
          icon={Clapperboard}
          title={hasActiveFilter ? 'Không tìm thấy phim phù hợp' : 'Chưa có phim nào'}
          description={
            hasActiveFilter
              ? 'Thử thay đổi từ khoá hoặc bộ lọc thể loại/quốc gia.'
              : 'Hệ thống chưa có phim nào để hiển thị.'
          }
        />
      ) : (
        <>
          <div className={isFetching ? 'opacity-60 transition-opacity' : 'transition-opacity'}>
            <MovieGrid movies={visibleMovies} />
          </div>
          {data ? (
            <DataPagination
              page={data.page}
              totalPages={data.totalPages}
              total={data.total}
              onPageChange={handlePageChange}
              disabled={isFetching}
              ariaLabel="Phân trang danh sách phim"
            />
          ) : null}
        </>
      )}
    </div>
  );
}
