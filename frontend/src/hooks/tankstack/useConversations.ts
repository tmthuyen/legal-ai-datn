import { legalChatApi } from '@/apis/legal.api';
import { parseAxiosError } from '@/lib/axiosClient';
import { Conversation } from '@/shared/types/legal.types';
import { Pagination } from '@/shared/types/api.types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

/** Kết quả danh sách hội thoại phân trang cho UI (items + pagination từ envelope). */
export interface ConversationsListResult {
  items: Conversation[];
  pagination: Pagination;
}

/** QueryKey gốc của domain hội thoại — invalidate theo root khi tạo/xóa/gửi tin. */
export const CONVERSATIONS_QUERY_KEY = 'legal-conversations';

/**
 * Danh sách hội thoại của người dùng hiện tại (`GET /chat/conversations`, có phân trang,
 * sắp xếp `updatedAt` giảm dần theo contract).
 */
export function useConversations(params: { page?: number; limit?: number; enabled?: boolean }) {
  const { page = 1, limit = 20, enabled = true } = params;
  return useQuery({
    queryKey: [CONVERSATIONS_QUERY_KEY, page, limit],
    queryFn: async (): Promise<ConversationsListResult> => {
      const response = await legalChatApi.getConversations({ page, limit });
      return { items: response.result ?? [], pagination: response.pagination };
    },
    enabled,
    staleTime: 1000 * 30,
    placeholderData: (previous) => previous,
  });
}

/** Tạo hội thoại mới (`POST /chat/conversations`) rồi invalidate danh sách. */
export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (title?: string) => legalChatApi.createConversation({ title }),
    onSuccess: (response) => {
      toast.success(response.message || 'Đã tạo cuộc trò chuyện mới.');
      queryClient.invalidateQueries({ queryKey: [CONVERSATIONS_QUERY_KEY] });
    },
    onError: (error) =>
      toast.error(parseAxiosError(error).message || 'Không thể tạo cuộc trò chuyện.'),
  });
}

/** Xóa hội thoại (`DELETE /chat/conversations/:id`) — chỉ chủ sở hữu. */
export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => legalChatApi.deleteConversation(id),
    onSuccess: (response) => {
      toast.success(response.message || 'Đã xóa cuộc trò chuyện.');
      queryClient.invalidateQueries({ queryKey: [CONVERSATIONS_QUERY_KEY] });
    },
    onError: (error) =>
      toast.error(parseAxiosError(error).message || 'Không thể xóa cuộc trò chuyện.'),
  });
}
