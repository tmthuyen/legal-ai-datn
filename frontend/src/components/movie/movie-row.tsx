'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { MovieCard } from './movie-card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { Movie } from '@/shared/types/movie.types';

interface MovieRowProps {
  movies: Movie[];
  /** Số card tối đa hiển thị trong 1 hàng (mặc định 12). */
  max?: number;
  className?: string;
}

/**
 * Hàng phim **1 hàng ngang** trên mọi kích thước màn hình:
 * 2 phim (mobile) → 3 (sm) → 4 (md) → 6 (lg), phần còn lại cuộn ngang
 * (scroll-snap, ẩn scrollbar). Desktop có nút cuộn trái/phải hiện khi hover.
 */
export function MovieRow({ movies, max = 12, className }: MovieRowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScroll, setCanScroll] = useState({ left: false, right: false });

  const updateScrollState = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScroll({
      left: el.scrollLeft > 4,
      right: el.scrollLeft + el.clientWidth < el.scrollWidth - 4,
    });
  }, []);

  useEffect(() => {
    updateScrollState();
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener('scroll', updateScrollState, { passive: true });
    window.addEventListener('resize', updateScrollState);
    return () => {
      el.removeEventListener('scroll', updateScrollState);
      window.removeEventListener('resize', updateScrollState);
    };
  }, [updateScrollState]);

  const scrollByCard = (direction: -1 | 1) => {
    const el = scrollRef.current;
    if (!el) return;
    const card = el.querySelector<HTMLElement>('[data-card]');
    const step = card ? card.offsetWidth + 12 : el.clientWidth * 0.8;
    el.scrollBy({ left: direction * step, behavior: 'smooth' });
  };

  if (movies.length === 0) return null;

  return (
    <div className="group/row relative">
      <div
        ref={scrollRef}
        className={cn(
          // 1 hàng ngang: 2 → 3 → 4 → 6 card, không wrap, ẩn scrollbar
          'no-scrollbar flex snap-x snap-mandatory gap-3 overflow-x-auto pb-1 md:gap-4',
          className,
        )}
        role="list"
      >
        {movies.slice(0, max).map((movie) => (
          <div
            key={movie.id}
            data-card
            role="listitem"
            className="w-[calc(50%-6px)] shrink-0 snap-start sm:w-[calc(33.333%-8px)] md:w-[calc(25%-12px)] lg:w-[calc(16.666%-14px)]"
          >
            <MovieCard movie={movie} />
          </div>
        ))}
      </div>

      {/* Nút cuộn (desktop, hiện khi hover row) */}
      {canScroll.left && (
        <Button
          type="button"
          variant="secondary"
          size="icon"
          aria-label="Cuộn sang trái"
          onClick={() => scrollByCard(-1)}
          className="absolute top-1/2 left-0 z-20 hidden size-9 -translate-y-1/2 rounded-full opacity-0 shadow-md transition-opacity group-hover/row:opacity-100 md:inline-flex"
        >
          <ChevronLeft className="size-5" aria-hidden="true" />
        </Button>
      )}
      {canScroll.right && (
        <Button
          type="button"
          variant="secondary"
          size="icon"
          aria-label="Cuộn sang phải"
          onClick={() => scrollByCard(1)}
          className="absolute top-1/2 right-0 z-20 hidden size-9 -translate-y-1/2 rounded-full opacity-0 shadow-md transition-opacity group-hover/row:opacity-100 md:inline-flex"
        >
          <ChevronRight className="size-5" aria-hidden="true" />
        </Button>
      )}
    </div>
  );
}

/** Skeleton cho `MovieRow` (1 hàng ngang). */
export function MovieRowSkeleton({ items = 6 }: { items?: number }) {
  return (
    <div className="flex gap-3 md:gap-4" aria-hidden="true">
      {Array.from({ length: items }).map((_, index) => (
        <div
          key={index}
          className="w-[calc(50%-6px)] shrink-0 sm:w-[calc(33.333%-8px)] md:w-[calc(25%-12px)] lg:w-[calc(16.666%-14px)]"
        >
          <Skeleton className="aspect-[2/3] w-full rounded-lg" />
          <Skeleton className="mt-2 h-4 w-3/4" />
          <Skeleton className="mt-1 h-3 w-1/2" />
        </div>
      ))}
    </div>
  );
}
