import { ratingApi } from '@/apis/rating.api';
import { parseAxiosError } from '@/lib/axiosClient';
import { Rating } from '@/shared/types/rating.types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

/** Danh sách đánh giá của một phim (public). */
export function useGetRatings(
  movieId: number | string,
  page: number = 1,
  limit: number = 5,
) {
  return useQuery({
    queryKey: ['ratings', String(movieId), page, limit],
    queryFn: async (): Promise<{ ratings: Rating[]; total: number; totalPages: number }> => {
      const response = await ratingApi.getByMovie(movieId, { page, limit });
      return {
        ratings: response.result ?? [],
        total: response.pagination?.total ?? 0,
        totalPages: response.pagination?.totalPages ?? 1,
      };
    },
    enabled: !!movieId,
    staleTime: 1000 * 60,
  });
}

/**
 * Gửi đánh giá sao (JWT) — `POST /api/ratings` (user chỉ đánh giá 1 lần/phim;
 * submit lại sẽ lỗi unique → hiển thị message từ server).
 */
export function useCreateRating(movieId: number | string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (rating: number): Promise<Rating> => {
      const response = await ratingApi.create({ rating, movieId });
      return response.result;
    },
    onSuccess: () => {
      toast.success('Cảm ơn bạn đã đánh giá!');
      queryClient.invalidateQueries({ queryKey: ['ratings', String(movieId)] });
      // Đồng bộ voteAverage/voteCount ở card/chi tiết
      queryClient.invalidateQueries({ queryKey: ['movie', String(movieId)] });
      queryClient.invalidateQueries({ queryKey: ['movies'] });
    },
    onError: (error) => {
      const parsedError = parseAxiosError(error);
      toast.error(parsedError.message || 'Không thể gửi đánh giá.');
    },
  });
}

const useRating = {
  useGetRatings,
  useCreateRating,
};

export default useRating;
