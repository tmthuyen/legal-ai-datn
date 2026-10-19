'use client';

import { Eye } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useMovieSocket } from '@/hooks/useMovieSocket';

interface MovieViewCountProps {
  movieId: number | string;
  /** Lượt xem ban đầu lấy từ `GET /api/movies/:id`. */
  viewCount?: number;
  className?: string;
}

/**
 * Hiển thị lượt xem của phim — cập nhật **realtime** qua WS event
 * `movie-{id}-viewCount` (không refetch API).
 */
export function MovieViewCount({ movieId, viewCount, className }: MovieViewCountProps) {
  const [count, setCount] = useState(Number(viewCount) || 0);

  useEffect(() => {
    setCount(Number(viewCount) || 0);
  }, [viewCount]);

  useMovieSocket({
    movieId,
    onViewCount: (payload) => {
      if (payload && payload.viewCount !== undefined) {
        setCount(Number(payload.viewCount) || 0);
      }
    },
  });

  return (
    <span className={className}>
      <Eye className="mr-1.5 inline size-4" aria-hidden="true" />
      {count.toLocaleString('vi-VN')} lượt xem
    </span>
  );
}
