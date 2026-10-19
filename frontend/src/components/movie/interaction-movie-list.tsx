'use client';

import { Clock, Film, Heart } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { useState } from 'react';
import { DataPagination } from '@/components/common/DataPagination';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import useInteraction from '@/hooks/tankstack/useInteraction';
import { cn } from '@/lib/utils';
import { Interaction } from '@/shared/types/interaction.types';
import { getMovieTitle, getPosterUrl, getReleaseYear } from '@/shared/utils/movie';

const PAGE_LIMIT = 12;

/** Nhãn + màu badge theo loại tương tác (history luôn là `click`; favorites hiển thị đúng type). Dùng lại ở trang admin Interaction. */
export const TYPE_BADGES: Record<string, { label: string; className: string }> = {
  click: { label: 'Đã xem', className: 'border-border text-muted-foreground' },
  like: { label: 'Thích', className: 'border-primary/30 bg-primary/10 text-primary' },
  dislike: { label: 'Không thích', className: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-500' },
  favorite: { label: 'Yêu thích', className: 'border-red-500/30 bg-red-500/10 text-red-500' },
  watchlist: { label: 'Muốn xem', className: 'border-amber-500/30 bg-amber-500/10 text-amber-500' },
};

function formatDate(value?: Date | string): string {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString('vi-VN');
}

function InteractionRow({ interaction }: { interaction: Interaction }) {
  const movie = interaction.movie;
  if (!movie) return null;

  const badge = TYPE_BADGES[interaction.type] ?? TYPE_BADGES.click;
  const poster = getPosterUrl(movie.posterPath || movie.backdropPath);
  const title = getMovieTitle(movie);
  const year = getReleaseYear(movie.releaseDate);
  const dateLabel = formatDate(interaction.createdAt);

  return (
    <li>
      <Link
        href={`/movies/${movie.id}`}
        className="group flex items-center gap-4 rounded-xl border bg-card p-3 transition-colors hover:border-primary/40 hover:bg-accent/50"
      >
        <div className="relative h-24 w-16 shrink-0 overflow-hidden rounded-lg bg-muted">
          {poster ? (
            <Image src={poster} alt="" fill sizes="64px" className="object-cover" />
          ) : (
            <Film
              className="text-muted-foreground absolute top-1/2 left-1/2 size-6 -translate-x-1/2 -translate-y-1/2"
              aria-hidden="true"
            />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="group-hover:text-primary truncate font-semibold transition-colors">
            {title}
            {year ? (
              <span className="text-muted-foreground ml-1.5 text-sm font-normal">({year})</span>
            ) : null}
          </p>
          <div className="mt-1.5 flex flex-wrap items-center gap-2 text-sm">
            <span
              className={cn('rounded-full border px-2 py-0.5 text-xs font-medium', badge.className)}
            >
              {badge.label}
            </span>
            {dateLabel ? <span className="text-muted-foreground">{dateLabel}</span> : null}
          </div>
        </div>
      </Link>
    </li>
  );
}

function InteractionListSkeleton() {
  return (
    <ul className="space-y-3" aria-hidden="true">
      {Array.from({ length: 5 }).map((_, index) => (
        <li key={index} className="flex items-center gap-4 rounded-xl border bg-card p-3">
          <Skeleton className="h-24 w-16 rounded-lg" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-5 w-2/3" />
            <Skeleton className="h-4 w-24" />
          </div>
        </li>
      ))}
    </ul>
  );
}

const SOURCE_CONFIG = {
  history: {
    emptyIcon: Clock,
    emptyTitle: 'Chưa có lịch sử xem',
    emptyDescription: 'Bạn chưa xem bộ phim nào. Hãy khám phá phim ngay!',
  },
  favorites: {
    emptyIcon: Heart,
    emptyTitle: 'Chưa có phim yêu thích',
    emptyDescription:
      'Hãy thích / yêu thích / muốn xem một bộ phim để chúng xuất hiện tại đây.',
  },
} as const;

interface MyInteractionListProps {
  /**
   * Nguồn dữ liệu: `history` (lịch sử xem — `type=click`) hoặc
   * `favorites` (like/favorite/watchlist) — gọi API tương ứng.
   */
  source: 'history' | 'favorites';
}

/**
 * Danh sách tương tác cá nhân **dùng chung** cho `/my-history` và `/my-favorites`
 * (1 điểm render — không duplicate code): hàng phim (poster + tên + badge loại
 * tương tác + ngày), click → `/movies/[id]`, phân trang `DataPagination`,
 * đầy đủ loading skeleton / empty / error state.
 */
export function MyInteractionList({ source }: MyInteractionListProps) {
  const [page, setPage] = useState(1);

  // Gọi cả hai hook (rules của React Hooks) — hook không được chọn sẽ `enabled=false` nên không fetch.
  const historyQuery = useInteraction.useMyHistory(page, PAGE_LIMIT, source === 'history');
  const favoritesQuery = useInteraction.useMyFavoritesPaged(
    page,
    PAGE_LIMIT,
    source === 'favorites',
  );

  const { data, isLoading, isError, isFetching, refetch } =
    source === 'history' ? historyQuery : favoritesQuery;

  const config = SOURCE_CONFIG[source];
  const items = data?.items ?? [];
  const pagination = data?.pagination;

  const handlePageChange = (nextPage: number) => {
    setPage(nextPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (isLoading) {
    return <InteractionListSkeleton />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Không thể tải danh sách"
        description="Vui lòng kiểm tra kết nối và thử lại."
        onRetry={() => refetch()}
      />
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        icon={config.emptyIcon}
        title={config.emptyTitle}
        description={config.emptyDescription}
        action={
          <Button asChild size="sm" className="cursor-pointer">
            <Link href="/movies">Khám phá phim</Link>
          </Button>
        }
      />
    );
  }

  return (
    <div className="flex w-full flex-col gap-6">
      <ul
        className={cn(
          'space-y-3 transition-opacity',
          isFetching ? 'opacity-60' : 'opacity-100',
        )}
      >
        {items.map((interaction) => (
          <InteractionRow key={interaction.id} interaction={interaction} />
        ))}
      </ul>

      {pagination ? (
        <DataPagination
          page={pagination.page}
          totalPages={pagination.totalPages}
          total={pagination.total}
          onPageChange={handlePageChange}
          disabled={isFetching}
          ariaLabel="Phân trang danh sách"
        />
      ) : null}
    </div>
  );
}
