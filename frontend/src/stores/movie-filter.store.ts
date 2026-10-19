import { create } from 'zustand';

export type MovieSortOption = 'newest' | 'rating' | 'popular';

export interface MovieFilterState {
  keyword: string;
  /** id thể loại dạng string (khớp value của Select), null = tất cả */
  genreId: string | null;
  /** id quốc gia dạng string (khớp value của Select), null = tất cả */
  countryId: string | null;
  sort: MovieSortOption;
  page: number;
  limit: number;
  /** Cập nhật một phần filter; mặc định quay về trang 1. */
  setFilter: (filter: Partial<Omit<MovieFilterState, 'setFilter' | 'setPage' | 'resetFilter'>>) => void;
  setPage: (page: number) => void;
  resetFilter: () => void;
}

const DEFAULT_FILTER = {
  keyword: '',
  genreId: null as string | null,
  countryId: null as string | null,
  sort: 'newest' as MovieSortOption,
  page: 1,
  limit: 24,
};

export const useMovieFilterStore = create<MovieFilterState>((set) => ({
  ...DEFAULT_FILTER,

  setFilter: (filter) =>
    set((state) => ({
      ...state,
      ...filter,
      page: filter.page ?? 1,
    })),

  setPage: (page) => set({ page }),

  resetFilter: () => set({ ...DEFAULT_FILTER }),
}));
