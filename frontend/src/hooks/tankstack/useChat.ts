import { legalChatApi } from '@/apis/legal.api';
import { parseAxiosError } from '@/lib/axiosClient';
import { ChatReply, Conversation, Message } from '@/shared/types/legal.types';
import { Pagination } from '@/shared/types/api.types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { toast } from 'sonner';
import {
  CONVERSATIONS_QUERY_KEY,
  useConversations,
  useCreateConversation,
} from './useConversations';

/** Kết quả lịch sử tin nhắn phân trang (items + pagination từ envelope). */
export interface MessagesListResult {
  items: Message[];
  pagination: Pagination;
}

/** Lịch sử tin nhắn của một hội thoại (`GET /chat/conversations/:id/messages`, `createdAt` tăng dần). */
export function useMessages(params: {
  conversationId: string | null;
  page?: number;
  limit?: number;
}) {
  const { conversationId, page = 1, limit = 50 } = params;
  return useQuery({
    queryKey: ['legal-messages', conversationId, page, limit],
    queryFn: async (): Promise<MessagesListResult> => {
      const response = await legalChatApi.getMessages(conversationId as string, { page, limit });
      return { items: response.result ?? [], pagination: response.pagination };
    },
    enabled: !!conversationId,
    staleTime: 1000 * 15,
  });
}

/**
 * Gửi câu hỏi pháp luật vào hội thoại (`POST /chat/conversations/:id/messages`).
 * Trả về `ChatReply` (userMessage + botMessage kèm citations).
 */
export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ conversationId, content }: { conversationId: string; content: string }) =>
      legalChatApi.sendMessage(conversationId, { content }),
    onSuccess: (response: { result: ChatReply }, variables) => {
      // Làm mới lịch sử tin nhắn của hội thoại và danh sách (cập nhật `updatedAt`).
      queryClient.invalidateQueries({ queryKey: ['legal-messages', variables.conversationId] });
      queryClient.invalidateQueries({ queryKey: [CONVERSATIONS_QUERY_KEY] });
      void response;
    },
    onError: (error, variables) => {
      // Services vẫn lưu message bot lỗi khi Backend không phản hồi (502) → refetch để hiển thị.
      queryClient.invalidateQueries({ queryKey: ['legal-messages', variables.conversationId] });
      toast.error(parseAxiosError(error).message || 'Không thể gửi câu hỏi. Vui lòng thử lại.');
    },
  });
}

/**
 * Hook tổng hợp cho trang hỏi đáp: gộp danh sách hội thoại + tin nhắn + gửi câu hỏi
 * và giữ `activeConversationId` nội bộ để UI không phải tự quản lý state phụ thuộc.
 */
export function useChat() {
  const queryClient = useQueryClient();
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  const conversationsQuery = useConversations({ page: 1, limit: 50 });
  const messagesQuery = useMessages({ conversationId: activeConversationId, page: 1, limit: 100 });
  const sendMessageMutation = useSendMessage();
  const createConversationMutation = useCreateConversation();

  /**
   * Tạo hội thoại mới (`POST /chat/conversations`) và trả về hội thoại vừa tạo
   * (hoặc `null` nếu thất bại) để caller chọn làm hội thoại đang mở.
   */
  const createConversation = async (title?: string): Promise<Conversation | null> => {
    try {
      const response = await createConversationMutation.mutateAsync(title);
      return response.result ?? null;
    } catch {
      return null;
    }
  };

  /** Gửi câu hỏi vào hội thoại chỉ định (mutation đã tự xử lý toast lỗi + invalidate). */
  const sendMessage = (payload: { conversationId: string; content: string }) =>
    sendMessageMutation.mutateAsync(payload);

  return {
    conversations: conversationsQuery.data?.items ?? [],
    conversationsLoading: conversationsQuery.isLoading,
    conversationsError: conversationsQuery.error,
    refetchConversations: conversationsQuery.refetch,
    activeConversationId,
    setActiveConversationId,
    messages: messagesQuery.data?.items ?? [],
    messagesLoading: messagesQuery.isLoading,
    messagesError: messagesQuery.error,
    refetchMessages: messagesQuery.refetch,
    sendMessage,
    isSending: sendMessageMutation.isPending,
    createConversation,
    isCreatingConversation: createConversationMutation.isPending,
    /** Invalidate toàn bộ domain chat (dùng sau khi xóa hội thoại từ nơi khác). */
    invalidateChat: () => queryClient.invalidateQueries({ queryKey: [CONVERSATIONS_QUERY_KEY] }),
  };
}
