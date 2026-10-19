'use client';

import { Sparkles } from 'lucide-react';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';

interface SimilarMoviesProps {
  /** Thể loại của phim hiện tại — dùng để gợi ý link khám phá cùng thể loại. */
  genres?: { id: number | string; name: string }[];
}

/**
 * **Placeholder** cho mục "Phim tương tự" — backend chưa có endpoint gợi ý
 * phim tương tự (chỉ có recommendation qua ai-service `/api/recommendations`).
 * Hiện tại hiển thị link khám phá theo thể loại của phim; khi backend có
 * endpoint sẽ thay thế bằng danh sách `MovieRow`.
 */
export function SimilarMovies({ genres = [] }: SimilarMoviesProps) {
  return (
    <section aria-label="Phim tương tự" className="space-y-3">
      <h2 className="flex items-center gap-2 text-xl font-bold">
        <Sparkles className="size-5" aria-hidden="true" />
        Phim tương tự
        <span className="text-muted-foreground text-sm font-normal">(chưa hoàn thiện)</span>
      </h2>
      <div className="bg-muted/40 flex flex-col items-start gap-3 rounded-xl border border-dashed p-5">
        <p className="text-muted-foreground text-sm">
          Tính năng gợi ý phim tương tự đang chờ backend bổ sung endpoint — tạm thời khám phá theo
          thể loại của phim này:
        </p>
        {genres.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {genres.map((genre) => (
              <Link key={genre.id} href={`/movies?genre=${genre.id}`}>
                <Badge variant="secondary" className="hover:bg-secondary/80 cursor-pointer transition-colors">
                  {genre.name}
                </Badge>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground text-sm">Phim chưa gắn thể loại.</p>
        )}
      </div>
    </section>
  );
}
