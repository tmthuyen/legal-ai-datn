'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Loader2, MessageSquarePlus, MessagesSquare, Trash2 } from 'lucide-react';
import RequireAuth from '@/components/auth/require-auth';
import { ChatMessageBubble } from '@/components/legal/chat-message-bubble';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { DataPagination } from '@/components/common/DataPagination';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useConversations,
  useCreateConversation,
  useDeleteConversation,
} from '@/hooks/tankstack/useConversations';
import { useMessages } from '@/hooks/tankstack/useChat';
import { Conversation } from '@/shared/types/legal.types';
import dateTimeUtils from '@/shared/utils/formatting';
import { cn } from '@/lib/utils';

const PAGE_SIZE = 10;

/** Nội dung trang quản lý hội thoại — yêu cầu đăng nhập. */
export function ConversationsClient() {
  return (
    <RequireAuth>
      <ConversationsManager />
    </RequireAuth>
  );
}

function ConversationsManager() {
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Conversation | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Conversation | null>(null);

  const list = useConversations({ page, limit: PAGE_SIZE });
  const createConversation = useCreateConversation();
  const deleteConversation = useDeleteConversation();

  const messages = useMessages({ conversationId: selected?.id ?? null, page: 1, limit: 100 });
  const items = list.data?.items ?? [];

  const handleCreate = async () => {
    const response = await createConversation.mutateAsync(undefined);
    if (response.result) {
      setSelected(response.result);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    const deletedId = deleteTarget.id;
    await deleteConversation.mutateAsync(deletedId);
    if (selected?.id === deletedId) setSelected(null);
    setDeleteTarget(null);
  };

  return (
    <div className="animate-fade-in flex w-full flex-col gap-6 pb-10">
      <PageHeader
        title="Hội thoại của tôi"
        description="Xem lại, tiếp tục hoặc xóa các cuộc hội thoại hỏi đáp pháp luật."
        actions={
          <Button onClick={handleCreate} disabled={createConversation.isPending}>
            {createConversation.isPending ? (
              <Loader2 className="mr-2 size-4 animate-spin" aria-hidden />
            ) : (
              <MessageSquarePlus className="mr-2 size-4" aria-hidden />
            )}
            Hội thoại mới
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Danh sách hội thoại */}
        <div className="flex flex-col gap-4 lg:col-span-1">
          {list.isLoading ? (
            <div className="flex flex-col gap-3">
              {[0, 1, 2, 3].map((index) => (
                <Skeleton key={index} className="h-20 w-full" />
              ))}
            </div>
          ) : list.isError ? (
            <ErrorState
              title="Không thể tải hội thoại"
              description="Vui lòng kiểm tra kết nối và thử lại."
              onRetry={() => list.refetch()}
            />
          ) : items.length === 0 ? (
            <EmptyState
              icon={MessagesSquare}
              title="Chưa có hội thoại nào"
              description="Tạo hội thoại mới để bắt đầu hỏi đáp pháp luật."
              action={
                <Button onClick={handleCreate} disabled={createConversation.isPending}>
                  <MessageSquarePlus className="mr-2 size-4" aria-hidden />
                  Tạo hội thoại
                </Button>
              }
            />
          ) : (
            <>
              <ul className="flex flex-col gap-2">
                {items.map((conversation) => (
                  <li key={conversation.id}>
                    <Card
                      role="button"
                      tabIndex={0}
                      onClick={() => setSelected(conversation)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault();
                          setSelected(conversation);
                        }
                      }}
                      className={cn(
                        'cursor-pointer gap-0 py-0 transition-colors',
                        selected?.id === conversation.id
                          ? 'border-primary ring-primary/30 ring-2'
                          : 'hover:bg-accent/50',
                      )}
                    >
                      <CardContent className="flex items-start gap-3 px-4 py-3">
                        <MessagesSquare className="text-primary mt-0.5 size-4 shrink-0" aria-hidden />
                        <div className="flex min-w-0 flex-1 flex-col gap-1">
                          <p className="truncate text-sm font-medium">{conversation.title}</p>
                          <p className="text-muted-foreground text-xs">
                            Cập nhật: {dateTimeUtils.formatDateTime(conversation.updatedAt)}
                          </p>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          aria-label={`Xóa hội thoại ${conversation.title}`}
                          className="text-muted-foreground hover:text-destructive size-8 shrink-0"
                          onClick={(event) => {
                            event.stopPropagation();
                            setDeleteTarget(conversation);
                          }}
                        >
                          <Trash2 className="size-4" aria-hidden />
                        </Button>
                      </CardContent>
                    </Card>
                  </li>
                ))}
              </ul>

              {list.data ? (
                <DataPagination
                  page={list.data.pagination.page}
                  totalPages={list.data.pagination.totalPages}
                  total={list.data.pagination.total}
                  onPageChange={setPage}
                  disabled={list.isFetching}
                  ariaLabel="Phân trang hội thoại"
                />
              ) : null}
            </>
          )}
        </div>

        {/* Lịch sử tin nhắn của hội thoại được chọn */}
        <div className="lg:col-span-2">
          <Card className="flex min-h-[50vh] flex-col gap-0 overflow-hidden py-0">
            <CardHeader className="border-b px-4 py-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <MessagesSquare className="text-primary size-4" aria-hidden />
                {selected ? selected.title : 'Lịch sử hội thoại'}
                {selected && messages.data ? (
                  <Badge variant="secondary" className="ml-1">
                    {messages.data.pagination.total} tin nhắn
                  </Badge>
                ) : null}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 px-4 py-4">
              {!selected ? (
                <EmptyState
                  title="Chọn một hội thoại"
                  description="Chọn hội thoại ở cột bên trái để xem lại toàn bộ câu hỏi và câu trả lời."
                />
              ) : messages.isLoading ? (
                <div className="flex flex-col gap-4">
                  {[0, 1, 2].map((index) => (
                    <Skeleton key={index} className="h-16 w-full" />
                  ))}
                </div>
              ) : messages.isError ? (
                <ErrorState
                  title="Không thể tải lịch sử tin nhắn"
                  description="Vui lòng thử lại."
                  onRetry={() => messages.refetch()}
                />
              ) : (messages.data?.items.length ?? 0) === 0 ? (
                <EmptyState
                  title="Hội thoại trống"
                  description="Hội thoại này chưa có tin nhắn nào."
                  action={
                    <Button asChild>
                      <Link href="/chat">Đặt câu hỏi ngay</Link>
                    </Button>
                  }
                />
              ) : (
                <div className="flex flex-col gap-5">
                  {messages.data?.items.map((message) => (
                    <ChatMessageBubble key={message.id} message={message} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <ConfirmDialog
        isOpen={deleteTarget !== null}
        title="Xóa hội thoại"
        description={`Bạn có chắc muốn xóa hội thoại "${deleteTarget?.title ?? ''}"? Hành động này không thể hoàn tác.`}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
        confirmText="Xóa"
      />
    </div>
  );
}
