import { movieApi } from '@/apis/movie.api';
import { parseAxiosError } from '@/lib/axiosClient';
import { MovieListResult, MovieQuery } from '@/shared/types/movie.types';
import { useMutation, useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';

// get list (public)
export function useGetMovies(
  params: MovieQuery = {},
  staleTime: number = 1000 * 60 * 5,
  gcTime: number = 1000 * 60 * 10,
) {
  const { page, limit, keyword } = params;
  return useQuery({
    queryKey: ['movies', page, limit, keyword],
    queryFn: async (): Promise<MovieListResult> => {
      const response = await movieApi.getAll(params);
      return {
        movies: response.result,
        total: response.pagination?.total ?? 0,
        page: response.pagination?.page ?? page ?? 1,
        limit: response.pagination?.limit ?? limit ?? 10,
        totalPages: response.pagination?.totalPages ?? 1,
      };
    },
    staleTime: staleTime, // 5 minutes
    gcTime: gcTime, // 10 minutes
  });
}

// get one (public)
export function useGetMovieDetail(
  id: number | string,
  staleTime: number = 1000 * 60 * 5,
  gcTime: number = 1000 * 60 * 10,
) {
  return useQuery({
    queryKey: ['movie', id],
    queryFn: async () => {
      const response = await movieApi.getById(id);
      return response.result;
    },
    enabled: !!id,
    staleTime: staleTime,
    gcTime: gcTime,
  });
}

// increment view (public, optional auth)
export function useIncrementView() {
  return useMutation({
    mutationFn: async (id: number | string) => {
      const response = await movieApi.incrementView(id);
      return response.result;
    },
    onError: (error: any) => {
      const parsedError = parseAxiosError(error);
      toast.error(parsedError.message || 'Không thể cập nhật lượt xem.');
    },
  });
}

const useMovie = {
  useGetMovies,
  useGetMovieDetail,
  useIncrementView,
};

export default useMovie;
