import { commentApi } from '@/apis/comment.api';
import { parseAxiosError } from '@/lib/axiosClient';
import { Comment } from '@/shared/types/comment.types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useAuthStore } from '@/stores/auth.store';

/** Bình luận của một phim — `parentId` undefined → root. */
export function useGetComments(
  movieId: number | string,
  options: { page?: number; limit?: number; parentId?: number | string } = {},
) {
  const { page = 1, limit = 5, parentId } = options;

  return useQuery({
    queryKey: [
      'comments',
      String(movieId),
      parentId ? String(parentId) : 'root',
      page,
      limit,
    ],
    queryFn: async (): Promise<{ comments: Comment[]; total: number; totalPages: number }> => {
      const response = await commentApi.getByMovie(movieId, { page, limit, parentId });
      return {
        comments: response.result ?? [],
        total: response.pagination?.total ?? 0,
        totalPages: response.pagination?.totalPages ?? 1,
      };
    },
    enabled: !!movieId,
    staleTime: 1000 * 30,
  });
}

/**
 * Gửi bình luận (JWT) — optimistic prepend vào danh sách root, rollback `onError`,
 * đồng bộ lại với server `onSettled`.
 */
export function useCreateComment(movieId: number | string) {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);

  return useMutation({
    mutationFn: async (input: {
      content: string;
      parentId?: number | string;
    }): Promise<Comment> => {
      const response = await commentApi.create({ ...input, movieId });
      return response.result;
    },
    onMutate: async ({ content }) => {
      await queryClient.cancelQueries({
        queryKey: ['comments', String(movieId), 'root'],
      });
      const previous = queryClient.getQueriesData<{
        comments: Comment[];
        total: number;
      }>({ queryKey: ['comments', String(movieId), 'root'] });

      // Optimistic: thêm comment tạm vào danh sách root (trang đầu)
      const rootKey = ['comments', String(movieId), 'root', 1];
      queryClient.setQueryData<{ comments: Comment[]; total: number }>(rootKey, (old) => {
        if (!old) return old;
        const optimistic: Comment = {
          id: -Date.now(),
          content,
          parentId: null,
          replyCount: 0,
          createdAt: new Date().toISOString(),
          user: user ? { id: user.id, fullName: user.fullName, avatarUrl: user.avatarUrl } : undefined,
        };
        return { ...old, comments: [optimistic, ...old.comments], total: old.total + 1 };
      });

      return { previous };
    },
    onError: (error, _variables, context) => {
      context?.previous?.forEach(([key, data]) => {
        if (data) queryClient.setQueryData(key, data);
      });
      const parsedError = parseAxiosError(error);
      toast.error(parsedError.message || 'Không thể gửi bình luận.');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', String(movieId)] });
    },
  });
}

const useComment = {
  useGetComments,
  useCreateComment,
};

export default useComment;
