'use client';

import { Search, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import useCountry from '@/hooks/tankstack/useCountry';
import useGenre from '@/hooks/tankstack/useGenre';
import { MovieSortOption, useMovieFilterStore } from '@/stores/movie-filter.store';

const ALL = 'all';

const SORT_OPTIONS: { value: MovieSortOption; label: string }[] = [
  { value: 'newest', label: 'Mới nhất' },
  { value: 'rating', label: 'Đánh giá cao' },
  { value: 'popular', label: 'Xem nhiều' },
];

export function MovieFilters() {
  const keyword = useMovieFilterStore((state) => state.keyword);
  const genreId = useMovieFilterStore((state) => state.genreId);
  const countryId = useMovieFilterStore((state) => state.countryId);
  const sort = useMovieFilterStore((state) => state.sort);
  const setFilter = useMovieFilterStore((state) => state.setFilter);
  const resetFilter = useMovieFilterStore((state) => state.resetFilter);

  const [keywordInput, setKeywordInput] = useState(keyword);

  // Đồng bộ khi store keyword thay đổi **từ bên ngoài** (vd. seed từ URL nhờ ô tìm
  // kiếm header) — nếu không, debounce bên dưới sẽ ghi đè keyword vừa seed bằng giá
  // trị input local cũ (rỗng) trong 400ms → tìm kiếm mất tác dụng.
  const prevKeyword = useRef(keyword);
  useEffect(() => {
    if (keyword !== prevKeyword.current) {
      prevKeyword.current = keyword;
      setKeywordInput(keyword);
    }
  }, [keyword]);

  // Debounce keyword ~400ms để tránh gọi API và đụng rate limit.
  useEffect(() => {
    const timer = setTimeout(() => {
      if (keywordInput !== keyword) {
        setFilter({ keyword: keywordInput });
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [keywordInput, keyword, setFilter]);

  const { data: genres, isLoading: isGenresLoading } = useGenre.useGetAll({ limit: 100 });
  const { data: countries, isLoading: isCountriesLoading } = useCountry.useGetCountries();

  const hasActiveFilter = !!keyword || !!genreId || !!countryId || sort !== 'newest';

  return (
    <div className="bg-card text-card-foreground flex flex-col gap-3 rounded-xl border p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2" />
          <Input
            value={keywordInput}
            onChange={(event) => setKeywordInput(event.target.value)}
            placeholder="Tìm phim theo tên..."
            className="h-11 pl-9"
            aria-label="Tìm phim theo tên"
          />
        </div>

        <Select
          value={genreId ?? ALL}
          onValueChange={(value) => setFilter({ genreId: value === ALL ? null : value })}
        >
          <SelectTrigger className="h-11 w-full md:w-44" aria-label="Lọc theo thể loại">
            <SelectValue placeholder="Thể loại" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Tất cả thể loại</SelectItem>
            {isGenresLoading && (
              <SelectItem value="__loading_genres" disabled>
                Đang tải...
              </SelectItem>
            )}
            {genres?.map((genre) => (
              <SelectItem key={genre.id} value={String(genre.id)}>
                {genre.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={countryId ?? ALL}
          onValueChange={(value) => setFilter({ countryId: value === ALL ? null : value })}
        >
          <SelectTrigger className="h-11 w-full md:w-44" aria-label="Lọc theo quốc gia">
            <SelectValue placeholder="Quốc gia" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Tất cả quốc gia</SelectItem>
            {isCountriesLoading && (
              <SelectItem value="__loading_countries" disabled>
                Đang tải...
              </SelectItem>
            )}
            {countries?.map((country) => (
              <SelectItem key={country.id} value={String(country.id)}>
                {country.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={sort} onValueChange={(value) => setFilter({ sort: value as MovieSortOption })}>
          <SelectTrigger className="h-11 w-full md:w-40" aria-label="Sắp xếp">
            <SelectValue placeholder="Sắp xếp" />
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {hasActiveFilter && (
          <Button
            variant="ghost"
            className="h-11"
            onClick={() => {
              setKeywordInput('');
              resetFilter();
            }}
          >
            <X /> Xoá lọc
          </Button>
        )}
      </div>
    </div>
  );
}
