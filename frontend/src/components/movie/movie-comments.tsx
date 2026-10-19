'use client';

import { MessageCircle, Send, CornerDownRight } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { DataPagination } from '@/components/common/DataPagination';
import { EmptyState } from '@/components/common/EmptyState';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import useComment from '@/hooks/tankstack/useComment';
import { useRequireLogin } from '@/hooks/useRequireLogin';
import { emitTypingComment, useMovieSocket } from '@/hooks/useMovieSocket';
import { cn } from '@/lib/utils';
import { Comment } from '@/shared/types/comment.types';
import { useAuthStore } from '@/stores/auth.store';

const PAGE_LIMIT = 5;

function timeAgo(iso?: string): string {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'vừa xong';
  if (minutes < 60) return `${minutes} phút trước`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} ngày trước`;
  return new Date(iso).toLocaleDateString('vi-VN');
}

function CommentItem({ comment }: { comment: Comment }) {
  const name = comment.user?.fullName || comment.user?.email || 'Người dùng';
  const isTemporary = comment.id < 0;

  return (
    <li className="flex gap-3">
      <Avatar className="size-9 shrink-0">
        {comment.user?.avatarUrl && <AvatarImage src={comment.user.avatarUrl} alt={name} />}
        <AvatarFallback>{name.charAt(0).toUpperCase()}</AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <div className="bg-muted/60 rounded-2xl rounded-tl-sm px-3.5 py-2.5">
          <div className="flex items-baseline gap-2">
            <span className="text-sm font-semibold">{name}</span>
            <span className="text-muted-foreground text-xs">{timeAgo(comment.createdAt)}</span>
            {isTemporary && <span className="text-muted-foreground text-xs">(đang gửi…)</span>}
          </div>
          <p className="text-foreground mt-0.5 text-sm whitespace-pre-wrap break-words">
            {comment.content}
          </p>
        </div>
      </div>
    </li>
  );
}

/** Danh sách reply (chỉ fetch khi user bấm "Xem trả lời"). */
function CommentReplies({ movieId, parentId }: { movieId: number | string; parentId: number | string }) {
  const { data, isLoading } = useComment.useGetComments(movieId, {
    parentId,
    limit: 20,
  });

  if (isLoading) {
    return (
      <div className="mt-2 space-y-2 pl-10" aria-hidden="true">
        <Skeleton className="h-12 w-full rounded-2xl" />
        <Skeleton className="h-12 w-5/6 rounded-2xl" />
      </div>
    );
  }

  const replies = data?.comments ?? [];
  if (replies.length === 0) return null;

  return (
    <ul className="mt-2 space-y-2 pl-10" aria-label="Trả lời">
      {replies.map((reply) => (
        <CommentItem key={reply.id} comment={reply} />
      ))}
    </ul>
  );
}

interface MovieCommentsProps {
  movieId: number | string;
}

/**
 * Khu vực bình luận của phim — danh sách root phân trang (`DataPagination`),
 * trả lời phân cấp (`parentId`), form gửi optimistic, và realtime qua WS
 * (`movie-{id}-comment` thêm bình luận mới, `movie-{id}-typing` hiển thị
 * "đang gõ…").
 */
export function MovieComments({ movieId }: MovieCommentsProps) {
  const requireLogin = useRequireLogin();
  const { isAuthenticated, user } = useAuthStore();

  const [page, setPage] = useState(1);
  const [content, setContent] = useState('');
  const [replyTo, setReplyTo] = useState<number | string | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [remoteTyping, setRemoteTyping] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<number | string>>(() => new Set());

  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useComment.useGetComments(movieId, { page, limit: PAGE_LIMIT });
  const createComment = useComment.useCreateComment(movieId);

  // Debounce sự kiện typingComment (chỉ emit khi đang gõ, dừng sau 2s im lặng)
  const notifyTyping = (isTyping: boolean) => {
    if (!isAuthenticated) return;
    emitTypingComment(movieId, isTyping, user?.fullName || undefined);
    if (typingTimer.current) clearTimeout(typingTimer.current);
    if (isTyping) {
      typingTimer.current = setTimeout(() => emitTypingComment(movieId, false), 2000);
    }
  };

  useEffect(() => {
    return () => {
      if (typingTimer.current) clearTimeout(typingTimer.current);
      emitTypingComment(movieId, false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Realtime: bình luận mới từ client khác → invalidate để refetch
  // (React Query tự dedupe theo queryKey, optimistic item cũng bị thay thế).
  const handleRemoteComment = (comment: Comment) => {
    if (comment.parentId) {
      // Bình luận trả lời → mở rộng reply list tương ứng
      setExpanded((prev) => new Set(prev).add(comment.parentId as number | string));
      queryClient.invalidateQueries({ queryKey: ['comments', String(movieId)] });
      return;
    }
    if (page === 1) {
      queryClient.invalidateQueries({
        queryKey: ['comments', String(movieId), 'root', page],
      });
    }
  };

  const handleTyping = (payload: { isTyping: boolean; userFullName: string }) => {
    setRemoteTyping(payload.isTyping ? payload.userFullName : null);
  };

  useMovieSocket({
    movieId,
    onComment: handleRemoteComment,
    onTyping: handleTyping,
  });

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!requireLogin()) return;
    const value = content.trim();
    if (!value || createComment.isPending) return;
    createComment.mutate(
      { content: value },
      {
        onSuccess: () => {
          setContent('');
          setPage(1);
          notifyTyping(false);
        },
      },
    );
  };

  const handleSubmitReply = (event: React.FormEvent) => {
    event.preventDefault();
    if (!requireLogin()) return;
    // Đã đăng nhập nhưng không có comment đang trả lời → bỏ qua (không redirect).
    if (replyTo === null) return;
    const value = replyContent.trim();
    if (!value || createComment.isPending) return;
    createComment.mutate(
      { content: value, parentId: replyTo },
      {
        onSuccess: () => {
          setReplyContent('');
          setReplyTo(null);
          if (replyTo !== null) setExpanded((prev) => new Set(prev).add(replyTo));
        },
      },
    );
  };

  const comments = data?.comments ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.totalPages ?? 1;

  return (
    <section aria-label="Bình luận" className="space-y-4">
      <h2 className="flex items-center gap-2 text-xl font-bold">
        <MessageCircle className="size-5" aria-hidden="true" />
        Bình luận <span className="text-muted-foreground font-normal">({total})</span>
      </h2>

      {/* Form bình luận gốc */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <Avatar className="size-9 shrink-0">
          {user?.avatarUrl && <AvatarImage src={user.avatarUrl} alt="" />}
          <AvatarFallback>{(user?.fullName || 'K').charAt(0).toUpperCase()}</AvatarFallback>
        </Avatar>
        <div className="flex-1 space-y-2">
          <Textarea
            value={content}
            onChange={(event) => {
              setContent(event.target.value);
              notifyTyping(event.target.value.length > 0);
            }}
            rows={2}
            maxLength={2000}
            placeholder={isAuthenticated ? 'Viết bình luận của bạn…' : 'Đăng nhập để bình luận…'}
            aria-label="Nội dung bình luận"
            className="min-h-16 resize-y"
          />
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground text-xs">{content.length}/2000</span>
            <Button
              type="submit"
              size="sm"
              disabled={!content.trim() || createComment.isPending}
              className="cursor-pointer"
            >
              <Send className="size-4" aria-hidden="true" />
              Gửi
            </Button>
          </div>
        </div>
      </form>

      {remoteTyping && (
        <p className="text-muted-foreground animate-pulse text-sm" role="status">
          {remoteTyping} đang gõ…
        </p>
      )}

      {/* Danh sách root comments */}
      {isLoading ? (
        <div className="space-y-3" aria-hidden="true">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="flex gap-3">
              <Skeleton className="size-9 rounded-full" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="h-14 w-full rounded-2xl" />
              </div>
            </div>
          ))}
        </div>
      ) : comments.length === 0 ? (
        <EmptyState
          icon={MessageCircle}
          title="Chưa có bình luận nào"
          description="Hãy là người đầu tiên bình luận về bộ phim này."
        />
      ) : (
        <>
          <ul className="space-y-4">
            {comments.map((comment) => {
              const replyCount = Number(comment.replyCount) || 0;
              const isExpanded = expanded.has(comment.id);
              return (
                <li key={comment.id} className="space-y-1">
                  <CommentItem comment={comment} />
                  <div className="flex items-center gap-3 pl-12">
                    <button
                      type="button"
                      onClick={() => {
                        if (replyTo === comment.id) {
                          setReplyTo(null);
                          setReplyContent('');
                        } else {
                          setReplyTo(comment.id);
                        }
                      }}
                      className={cn(
                        'text-muted-foreground hover:text-foreground inline-flex items-center gap-1 text-xs font-medium transition-colors',
                        'cursor-pointer',
                      )}
                      aria-expanded={replyTo === comment.id}
                    >
                      <CornerDownRight className="size-3.5" aria-hidden="true" />
                      Trả lời
                    </button>
                    {replyCount > 0 && !isExpanded && (
                      <button
                        type="button"
                        onClick={() => setExpanded((prev) => new Set(prev).add(comment.id))}
                        className="text-primary hover:text-primary/80 cursor-pointer text-xs font-medium transition-colors"
                      >
                        Xem {replyCount} trả lời
                      </button>
                    )}
                  </div>

                  {replyTo === comment.id && (
                    <form onSubmit={handleSubmitReply} className="mt-2 flex gap-2 pl-12">
                      <Input
                        value={replyContent}
                        onChange={(event) => setReplyContent(event.target.value)}
                        placeholder="Viết trả lời…"
                        aria-label="Nội dung trả lời"
                        maxLength={2000}
                        className="min-h-9 flex-1"
                      />
                      <Button
                        type="submit"
                        size="sm"
                        disabled={!replyContent.trim() || createComment.isPending}
                        className="cursor-pointer"
                      >
                        Trả lời
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setReplyTo(null);
                          setReplyContent('');
                        }}
                        className="cursor-pointer"
                      >
                        Hủy
                      </Button>
                    </form>
                  )}

                  {isExpanded && <CommentReplies movieId={movieId} parentId={comment.id} />}
                </li>
              );
            })}
          </ul>

          {totalPages > 1 && (
            <DataPagination
              page={page}
              totalPages={totalPages}
              total={total}
              onPageChange={setPage}
              ariaLabel="Phân trang bình luận"
            />
          )}
        </>
      )}
    </section>
  );
}
