'use client';

import { Calendar, Clapperboard, Film, Globe } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import Markdown from 'react-markdown';
import { MovieActions } from './movie-actions';
import { MovieViewCount } from './movie-view-count';
import { Badge } from '@/components/ui/badge';
import { MovieDetail as MovieDetailType } from '@/shared/types/movie.types';
import { getMovieTitle, getPosterUrl, getReleaseYear } from '@/shared/utils/movie';

/**
 * Thông tin chính của phim trên trang `/movies/[id]`:
 * poster, tiêu đề (EN + VI), metadata, mô tả (markdown), thể loại, quốc gia.
 */
export function MovieDetail({ movie }: { movie: MovieDetailType }) {
  const poster = getPosterUrl(movie.posterPath || movie.backdropPath);
  const title = getMovieTitle(movie);
  const overview = movie.overviewVi || movie.overview || '';
  const genres = movie.genres ?? [];
  const year = getReleaseYear(movie.releaseDate);
  const rating = typeof movie.voteAverage === 'number' ? movie.voteAverage : 0;
  const voteCount = Number(movie.voteCount) || 0;

  return (
    <section className="overflow-hidden rounded-2xl border bg-card shadow-sm">
      <div className="grid gap-6 p-6 md:grid-cols-[280px_1fr] md:p-8">
        {/* Poster */}
        <div className="bg-muted relative aspect-[2/3] w-full self-start overflow-hidden rounded-xl shadow-lg md:max-w-[280px]">
          {poster ? (
            <Image
              src={poster}
              alt={title}
              fill
              priority
              sizes="(max-width: 768px) 100vw, 280px"
              className="object-cover"
            />
          ) : (
            <div className="text-muted-foreground flex h-full w-full items-center justify-center">
              <Film className="size-12" />
            </div>
          )}
        </div>

        {/* Thông tin */}
        <div className="flex flex-col gap-4">
          <div>
            {movie.titleVi && movie.title && (
              <p className="text-muted-foreground text-sm font-medium">{movie.title}</p>
            )}
            <h1 className="text-3xl font-extrabold tracking-tight md:text-4xl">{title}</h1>
          </div>

          <div className="text-muted-foreground flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
            {year && (
              <span className="inline-flex items-center gap-1.5">
                <Calendar className="size-4" aria-hidden="true" />
                {year}
              </span>
            )}
            {movie.country && (
              <span className="inline-flex items-center gap-1.5">
                <Globe className="size-4" aria-hidden="true" />
                {movie.country.name}
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 font-medium text-foreground">
              <Clapperboard className="size-4 text-yellow-500" aria-hidden="true" />
              {rating.toFixed(1)} <span className="text-muted-foreground">/ {voteCount} đánh giá</span>
            </span>
            <MovieViewCount movieId={movie.id} viewCount={movie.viewCount} />
          </div>

          {genres.length > 0 && (
            <div className="flex flex-wrap gap-2" aria-label="Thể loại">
              {genres.map((genre) => (
                <Link key={genre.id} href={`/movies?genre=${genre.id}`}>
                  <Badge variant="secondary" className="hover:bg-secondary/80 cursor-pointer transition-colors">
                    {genre.name}
                  </Badge>
                </Link>
              ))}
            </div>
          )}

          {/* Bộ nút tương tác (thích / yêu thích / muốn xem) */}
          <MovieActions movieId={movie.id} variant="detail" className="mt-1" />

          {overview && (
            <div className="text-muted-foreground max-w-none text-sm leading-relaxed [&_a]:text-primary [&_a]:underline [&_li]:ml-4 [&_li]:list-disc [&_ol]:list-decimal [&_ol]:ml-5 [&_p]:mb-2 [&_strong]:text-foreground">
              <Markdown>{overview}</Markdown>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
