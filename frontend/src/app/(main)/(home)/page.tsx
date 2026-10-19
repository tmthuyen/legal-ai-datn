'use client';

import {
  ArrowRight,
  Play,
  Star,
  Eye,
  Crown,
  Calendar,
} from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { useMemo } from 'react';
import { SectionHeader } from '@/components/common/SectionHeader';
import { MovieRow, MovieRowSkeleton } from '@/components/movie/movie-row';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import useMovie from '@/hooks/tankstack/useMovie';
import useGenre from '@/hooks/tankstack/useGenre';
import useCountry from '@/hooks/tankstack/useCountry';
import { getMovieTitle, getPosterUrl, getReleaseYear } from '@/shared/utils/movie';
import { useAuthStore } from '@/stores/auth.store';

function HeroCarouselSkeleton() {
  return (
    <section className="from-primary/10 to-primary/5 relative overflow-hidden rounded-2xl border bg-gradient-to-br">
      <div className="grid gap-6 p-6 md:grid-cols-2 md:p-10">
        <div className="flex flex-col justify-center gap-4">
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-10 w-40" />
        </div>
        <Skeleton className="aspect-[2/3] w-full rounded-xl md:aspect-video" />
      </div>
    </section>
  );
}

function TopMovieCard({ movie, rank }: { movie: any; rank: number }) {
  const poster = getPosterUrl(movie.posterPath || movie.backdropPath);
  const title = getMovieTitle(movie);
  const year = getReleaseYear(movie.releaseDate);
  const rating = typeof movie.voteAverage === 'number' ? movie.voteAverage : 0;
  const views = Number(movie.viewCount) || 0;

  return (
    <Link href={`/movies/${movie.id}`} className="group block">
      <article className="relative overflow-hidden rounded-lg border bg-card shadow-sm transition-transform hover:-translate-y-1 hover:shadow-lg">
        <div className="relative aspect-[2/3] w-full">
          {poster ? (
            <Image
              src={poster}
              alt={title}
              fill
              className="object-cover transition-transform duration-300 group-hover:scale-105"
              sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
            />
          ) : (
            <div className="bg-muted flex h-full w-full items-center justify-center">
              <Play className="text-muted-foreground size-8" />
            </div>
          )}
          <div className="absolute top-3 left-3 flex items-center gap-2">
            <div className="flex items-center gap-1 rounded-full bg-black/70 px-2 py-1 text-xs font-semibold text-white">
              <Crown className="size-3" />
              Top {rank}
            </div>
          </div>
          <div className="absolute top-3 right-3 flex items-center gap-1 rounded-full bg-black/70 px-2 py-1 text-xs text-white">
            <Star className="size-3 fill-yellow-400 text-yellow-400" />
            {rating.toFixed(1)}
          </div>
          <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-3">
            <h3 className="line-clamp-2 font-semibold text-white">{title}</h3>
            <div className="mt-1 flex items-center gap-3 text-xs text-white/80">
              {year && (
                <span className="flex items-center gap-1">
                  <Calendar className="size-3" />
                  {year}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Eye className="size-3" />
                {views.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </article>
    </Link>
  );
}

/** Section danh sách phim theo **1 hàng ngang** (cuộn ngang, responsive 2→6 card). */
function MovieRowSection({
  title,
  description,
  href,
  movies,
  isLoading,
}: {
  title: string;
  description?: string;
  href?: string;
  movies?: any[];
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <section className="space-y-4">
        <SectionHeader title={title} description={description} />
        <MovieRowSkeleton />
      </section>
    );
  }

  if (!movies || movies.length === 0) {
    return null;
  }

  return (
    <section className="space-y-4">
      <SectionHeader
        title={title}
        description={description}
        action={
          href ? (
            <Link
              href={href}
              className="text-primary inline-flex shrink-0 items-center gap-1 text-sm font-medium hover:underline"
            >
              Xem tất cả <ArrowRight className="size-4" />
            </Link>
          ) : undefined
        }
      />
      <MovieRow movies={movies} max={12} />
    </section>
  );
}

function GenreSection() {
  const { data: genres, isLoading } = useGenre.useGetAll({ limit: 100 });

  if (isLoading) {
    return (
      <section className="space-y-4">
        <SectionHeader title="Khám phá theo thể loại" />
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton key={i} className="h-9 w-24 rounded-full" />
          ))}
        </div>
      </section>
    );
  }

  if (!genres || genres.length === 0) {
    return null;
  }

  return (
    <section className="space-y-4">
      <SectionHeader title="Khám phá theo thể loại" />
      <div className="flex flex-wrap gap-2">
        {genres.slice(0, 20).map((genre: any) => (
          <Link
            key={genre.id}
            href={`/movies?genre=${genre.id}`}
            className="bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded-full border px-4 py-2 text-sm font-medium transition-colors"
          >
            {genre.name}
          </Link>
        ))}
      </div>
    </section>
  );
}

function CountrySection() {
  const { data: countries, isLoading } = useCountry.useGetCountries();

  if (isLoading) {
    return (
      <section className="space-y-4">
        <SectionHeader title="Phim theo quốc gia" />
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-9 w-20 rounded-full" />
          ))}
        </div>
      </section>
    );
  }

  if (!countries || countries.length === 0) {
    return null;
  }

  return (
    <section className="space-y-4">
      <SectionHeader title="Phim theo quốc gia" />
      <div className="flex flex-wrap gap-2">
        {countries.slice(0, 10).map((country: any) => (
          <Link
            key={country.id}
            href={`/movies?country=${country.id}`}
            className="bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded-full border px-4 py-2 text-sm font-medium transition-colors"
          >
            {country.name}
          </Link>
        ))}
      </div>
    </section>
  );
}

export default function HomePage() {
  const { data: moviesData, isLoading: isMoviesLoading } = useMovie.useGetMovies({
    page: 1,
    limit: 24,
  });
  const movies = moviesData?.movies ?? [];
  const { isAuthenticated, user } = useAuthStore();

  const { topRated, mostViewed, newest } = useMemo(() => {
    const sortedByRating = [...movies].sort((a, b) => (b.voteAverage ?? 0) - (a.voteAverage ?? 0));
    const sortedByViews = [...movies].sort(
      (a, b) => (Number(b.viewCount) || 0) - (Number(a.viewCount) || 0),
    );
    const sortedByNewest = [...movies].sort((a, b) => {
      const dateA = new Date(a.releaseDate || a.createdAt).getTime();
      const dateB = new Date(b.releaseDate || b.createdAt).getTime();
      return dateB - dateA;
    });

    return {
      topRated: sortedByRating.slice(0, 6),
      mostViewed: sortedByViews.slice(0, 12),
      newest: sortedByNewest.slice(0, 12),
    };
  }, [movies]);

  return (
    <div className="animate-fade-in w-full space-y-10 pb-10">
      {isMoviesLoading ? (
        <HeroCarouselSkeleton />
      ) : (
        <section className="from-primary/10 via-primary/5 to-background relative overflow-hidden rounded-2xl border bg-gradient-to-br">
          <div className="grid gap-6 p-6 md:grid-cols-2 md:p-10">
            <div className="flex flex-col justify-center gap-4">
              <div className="space-y-2">
                <h1 className="text-3xl font-extrabold tracking-tight md:text-4xl lg:text-5xl">
                  Khám phá thế giới điện ảnh
                </h1>
                <p className="text-muted-foreground max-w-xl text-lg">
                  Tìm kiếm phim theo tên, thể loại và quốc gia. Đánh giá, bình luận và xây dựng danh
                  sách phim yêu thích của bạn.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button asChild size="lg">
                  <Link href="/movies">
                    Khám phá phim <ArrowRight className="ml-2 size-4" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg">
                  <Link href="/search">Tìm kiếm nâng cao</Link>
                </Button>
              </div>
              {topRated.length > 0 && (
                <div className="mt-4">
                  <p className="text-muted-foreground text-sm font-medium">Top đánh giá</p>
                  <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-3">
                    {topRated.slice(0, 3).map((movie, idx) => (
                      <TopMovieCard key={movie.id} movie={movie} rank={idx + 1} />
                    ))}
                  </div>
                </div>
              )}
            </div>
            {newest.length > 0 && (
              <div className="relative hidden md:block">
                <div className="relative aspect-[2/3] overflow-hidden rounded-xl shadow-2xl">
                  {getPosterUrl(newest[0].posterPath || newest[0].backdropPath) ? (
                    <Image
                      src={getPosterUrl(newest[0].posterPath || newest[0].backdropPath) as string}
                      alt={getMovieTitle(newest[0])}
                      fill
                      className="object-cover"
                      sizes="(max-width: 1024px) 50vw, 40vw"
                      priority
                    />
                  ) : null}
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent p-6">
                    <h2 className="text-xl font-bold text-white">{getMovieTitle(newest[0])}</h2>
                    <div className="mt-2 flex items-center gap-4 text-sm text-white/80">
                      {getReleaseYear(newest[0].releaseDate) && (
                        <span>{getReleaseYear(newest[0].releaseDate)}</span>
                      )}
                      <span className="flex items-center gap-1">
                        <Star className="size-4 fill-yellow-400 text-yellow-400" />
                        {(newest[0].voteAverage ?? 0).toFixed(1)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="size-4" />
                        {(Number(newest[0].viewCount) || 0).toLocaleString()}
                      </span>
                    </div>
                    <Button asChild className="mt-4" size="sm">
                      <Link href={`/movies/${newest[0].id}`}>
                        Xem chi tiết <ArrowRight className="ml-2 size-4" />
                      </Link>
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {isAuthenticated && (
        <MovieRowSection
          title={`Dành cho bạn, ${user?.fullName || 'thành viên'}`}
          description="Gợi ý dựa trên sở thích và hoạt động gần đây"
          href="/recommendations"
          movies={newest.slice(0, 6)}
          isLoading={isMoviesLoading}
        />
      )}

      <MovieRowSection
        title="Phim mới nhất"
        description="Những bộ phim vừa được cập nhật"
        href="/movies?sort=newest"
        movies={newest}
        isLoading={isMoviesLoading}
      />

      <MovieRowSection
        title="Được xem nhiều nhất"
        description="Những bộ phim được yêu thích nhất hệ thống"
        href="/movies?sort=popular"
        movies={mostViewed}
        isLoading={isMoviesLoading}
      />

      <MovieRowSection
        title="Đánh giá cao nhất"
        description="Những tác phẩm điện ảnh xuất sắc"
        href="/movies?sort=rating"
        movies={topRated}
        isLoading={isMoviesLoading}
      />

      <GenreSection />

      <CountrySection />

      <section className="space-y-4">
        <SectionHeader
          title="Top bình luận (Chưa hoàn thiện)"
          description="Những bình luận được yêu thích nhất"
          action={
            <Link
              href="/movies"
              className="text-primary inline-flex shrink-0 items-center gap-1 text-sm font-medium hover:underline"
            >
              Khám phá thêm <ArrowRight className="size-4" />
            </Link>
          }
        />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-4">
              <div className="flex items-start gap-3">
                <Skeleton className="size-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-1/3" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-3/4" />
                  <div className="flex items-center gap-4">
                    <Skeleton className="h-3 w-12" />
                    <Skeleton className="h-3 w-16" />
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <SectionHeader title="Sắp ra mắt" description="Những bộ phim sắp được công chiếu" />
        <MovieRow movies={newest.slice(0, 12)} max={12} />
      </section>
    </div>
  );
}
