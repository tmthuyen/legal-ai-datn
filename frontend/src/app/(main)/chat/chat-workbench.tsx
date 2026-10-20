'use client';

import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2, MessageSquarePlus, MessagesSquare, Send, Sparkles } from 'lucide-react';
import RequireAuth from '@/components/auth/require-auth';
import { ChatMessageBubble } from '@/components/legal/chat-message-bubble';
import { PageHeader } from '@/components/common/PageHeader';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { useChat } from '@/hooks/tankstack/useChat';
import { Message } from '@/shared/types/legal.types';
import { cn } from '@/lib/utils';

/** Vài câu hỏi gợi ý cho người dùng mới (chỉ để seed input, không phải dữ liệu API). */
const SUGGESTED_QUESTIONS = [
  'Điều 1 Hiến pháp 2013 quy định gì?',
  'Thừa kế theo pháp luật được chia như thế nào?',
  'Quy định về bảo đảm thực hiện nghĩa vụ theo Nghị định 21/2021?',
];

/**
 * Nội dung trang hỏi đáp: chọn/tạo hội thoại → gửi câu hỏi → xem câu trả lời kèm trích dẫn.
 * Yêu cầu đăng nhập (mọi endpoint `/chat/*` cần Bearer).
 */
export function ChatWorkbench() {
  return (
    <RequireAuth>
      <ChatSession />
    </RequireAuth>
  );
}

function ChatSession() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialQuestion = searchParams.get('q') ?? '';

  const {
    conversations,
    conversationsLoading,
    conversationsError,
    refetchConversations,
    activeConversationId,
    setActiveConversationId,
    messages,
    messagesLoading,
    messagesError,
    refetchMessages,
    sendMessage,
    isSending,
    createConversation,
    isCreatingConversation,
  } = useChat();

  const [input, setInput] = useState(initialQuestion);
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastMessageCount = useRef(0);

  const lastMessageId = messages.at(-1)?.id ?? null;

  // Tự cuộn xuống tin nhắn mới nhất khi số lượng thay đổi.
  useEffect(() => {
    if (messages.length !== lastMessageCount.current) {
      lastMessageCount.current = messages.length;
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages.length, lastMessageId]);

  const suggested = useMemo(
    () => SUGGESTED_QUESTIONS.filter((question) => question !== input),
    [input],
  );

  const handleCreate = async () => {
    const conversation = await createConversation();
    if (conversation) {
      setActiveConversationId(conversation.id);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const content = input.trim();
    if (!content || isSending) return;

    let conversationId = activeConversationId;
    if (!conversationId) {
      const conversation = await createConversation();
      if (!conversation) return;
      conversationId = conversation.id;
      setActiveConversationId(conversation.id);
    }

    setInput('');
    await sendMessage({ conversationId, content });
    // Đồng bộ URL để câu hỏi đầu tiên có thể chia sẻ/tải lại.
    router.replace(`/chat?q=${encodeURIComponent(content)}`);
  };

  if (conversationsError) {
    return (
      <div className="animate-fade-in w-full space-y-6 pb-10">
        <PageHeader
          title="Hỏi đáp pháp luật"
          description="Đặt câu hỏi và nhận câu trả lời kèm trích dẫn điều luật."
        />
        <ErrorState
          title="Không thể tải danh sách hội thoại"
          description="Vui lòng kiểm tra kết nối tới dịch vụ và thử lại."
          onRetry={() => refetchConversations()}
        />
      </div>
    );
  }

  return (
    <div className="animate-fade-in flex w-full flex-col gap-6 pb-10">
      <PageHeader
        title="Hỏi đáp pháp luật"
        description="Đặt câu hỏi bằng tiếng Việt, nhận câu trả lời kèm trích dẫn Điều/Khoản/Điểm."
        actions={
          <Button
            type="button"
            variant="outline"
            onClick={handleCreate}
            disabled={isCreatingConversation}
          >
            {isCreatingConversation ? (
              <Loader2 className="mr-2 size-4 animate-spin" aria-hidden />
            ) : (
              <MessageSquarePlus className="mr-2 size-4" aria-hidden />
            )}
            Hội thoại mới
          </Button>
        }
      />

      {/* Chọn hội thoại */}
      <Card className="gap-0 py-0">
        <CardContent className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center">
          <span className="text-muted-foreground shrink-0 text-sm font-medium">Hội thoại</span>
          {conversationsLoading ? (
            <Skeleton className="h-9 w-full sm:max-w-sm" />
          ) : conversations.length === 0 ? (
            <span className="text-muted-foreground text-sm">
              Chưa có hội thoại nào — hãy đặt câu hỏi đầu tiên bên dưới.
            </span>
          ) : (
            <Select
              value={activeConversationId ?? undefined}
              onValueChange={(value) => setActiveConversationId(value)}
            >
              <SelectTrigger className="w-full cursor-pointer sm:max-w-sm" aria-label="Chọn hội thoại">
                <SelectValue placeholder="Chọn một hội thoại" />
              </SelectTrigger>
              <SelectContent>
                {conversations.map((conversation) => (
                  <SelectItem key={conversation.id} value={conversation.id}>
                    {conversation.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="ms-auto cursor-pointer"
            asChild
          >
            <a href="/conversations">Quản lý hội thoại</a>
          </Button>
        </CardContent>
      </Card>

      {/* Khung hội thoại */}
      <Card className="flex min-h-[60vh] flex-col gap-0 overflow-hidden py-0">
        <CardHeader className="border-b px-4 py-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <MessagesSquare className="text-primary size-4" aria-hidden />
            Nội dung hội thoại
            {messages.length > 0 ? (
              <Badge variant="secondary" className="ml-1">
                {messages.length} tin nhắn
              </Badge>
            ) : null}
          </CardTitle>
        </CardHeader>

        <CardContent className="flex flex-1 flex-col gap-4 p-0">
          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
            {!activeConversationId ? (
              <EmptyState
                icon={Sparkles}
                title="Bắt đầu đặt câu hỏi"
                description="Nhập câu hỏi về Hiến pháp, Bộ luật Dân sự hoặc các nghị định, nghị quyết trong phạm vi hỗ trợ."
              />
            ) : messagesLoading ? (
              <div className="flex flex-col gap-4">
                {[0, 1, 2].map((index) => (
                  <Skeleton key={index} className="h-16 w-full" />
                ))}
              </div>
            ) : messagesError ? (
              <ErrorState
                title="Không thể tải lịch sử tin nhắn"
                description="Vui lòng thử lại."
                onRetry={() => refetchMessages()}
              />
            ) : messages.length === 0 ? (
              <EmptyState
                title="Hội thoại trống"
                description="Hãy đặt câu hỏi đầu tiên cho trợ lý pháp lý."
              />
            ) : (
              <div className="flex flex-col gap-5">
                {messages.map((message: Message) => (
                  <ChatMessageBubble key={message.id} message={message} />
                ))}
                {isSending ? (
                  <div className="text-muted-foreground flex items-center gap-2 px-2 text-sm">
                    <Loader2 className="size-4 animate-spin" aria-hidden />
                    Đang tra cứu và tổng hợp câu trả lời…
                  </div>
                ) : null}
              </div>
            )}
          </div>

          {/* Ô nhập câu hỏi */}
          <div className="border-t px-4 py-3">
            {messages.length === 0 && !activeConversationId ? (
              <div className="mb-2 flex flex-wrap gap-2">
                {suggested.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => setInput(question)}
                    className="bg-muted/60 hover:bg-muted cursor-pointer rounded-full border px-3 py-1 text-xs transition-colors"
                  >
                    {question}
                  </button>
                ))}
              </div>
            ) : null}

            <form onSubmit={handleSubmit} className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    event.currentTarget.form?.requestSubmit();
                  }
                }}
                rows={2}
                placeholder="Nhập câu hỏi pháp luật… (Enter để gửi, Shift+Enter xuống dòng)"
                aria-label="Câu hỏi pháp luật"
                className={cn(
                  'border-input bg-background min-h-11 w-full resize-none rounded-lg border px-3 py-2 text-sm outline-none transition-colors',
                  'placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-2',
                )}
              />
              <Button
                type="submit"
                className="h-11 shrink-0 cursor-pointer"
                disabled={isSending || input.trim().length === 0}
              >
                {isSending ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden />
                ) : (
                  <Send className="size-4" aria-hidden />
                )}
                <span className="sr-only">Gửi câu hỏi</span>
              </Button>
            </form>
            <p className="text-muted-foreground mt-2 text-xs">
              Câu trả lời của trợ lý mang tính tham khảo, kèm trích dẫn điều luật để bạn đối chiếu.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
