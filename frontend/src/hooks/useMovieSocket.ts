'use client';

import { useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

/**
 * URL của Socket.IO — backend chạy HTTP API + WS cùng cổng (8081).
 * Derive từ `NEXT_PUBLIC_API_BASE_URL` (bỏ hậu tố `/api`) — không hardcode cổng.
 */
function getSocketUrl(): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8081/api';
  return baseUrl.replace(/\/api\/?$/, '');
}

/** Socket dùng chung cho các thao tác emit (gõ bình luận…). */
let sharedSocket: Socket | null = null;
function getSharedSocket(): Socket {
  if (!sharedSocket) {
    sharedSocket = io(getSocketUrl(), {
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5,
    });
  }
  return sharedSocket;
}

export interface MovieTypingPayload {
  isTyping: boolean;
  userFullName: string;
}

export interface MovieViewCountPayload {
  movieId: number | string;
  viewCount: number;
}

export interface MovieRatingPayload {
  movieStats?: { voteCount: number; voteAverage: number };
  [key: string]: any;
}

interface UseMovieSocketOptions {
  movieId: number | string;
  onComment?: (comment: any) => void;
  onRating?: (payload: MovieRatingPayload) => void;
  onViewCount?: (payload: MovieViewCountPayload) => void;
  onTyping?: (payload: MovieTypingPayload) => void;
}

/**
 * Kết nối Socket.IO tới backend và subscribe các event realtime theo phim:
 * `movie-{id}-comment`, `movie-{id}-rating`, `movie-{id}-viewCount`,
 * `movie-{id}-typing`. Cleanup khi unmount.
 *
 * Handler được giữ trong ref nên callback mới không gây reconnect.
 */
export function useMovieSocket({
  movieId,
  onComment,
  onRating,
  onViewCount,
  onTyping,
}: UseMovieSocketOptions) {
  const socketRef = useRef<Socket | null>(null);
  const handlersRef = useRef({ onComment, onRating, onViewCount, onTyping });
  // Cập nhật handler ref trong effect (không ghi ref trong render — react-hooks/refs)
  useEffect(() => {
    handlersRef.current = { onComment, onRating, onViewCount, onTyping };
  });

  useEffect(() => {
    if (!movieId) return;

    const socket = io(getSocketUrl(), {
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5,
    });
    socketRef.current = socket;

    const commentEvent = `movie-${movieId}-comment`;
    const ratingEvent = `movie-${movieId}-rating`;
    const viewCountEvent = `movie-${movieId}-viewCount`;
    const typingEvent = `movie-${movieId}-typing`;

    socket.on(commentEvent, (comment: any) => handlersRef.current.onComment?.(comment));
    socket.on(ratingEvent, (payload: MovieRatingPayload) =>
      handlersRef.current.onRating?.(payload),
    );
    socket.on(viewCountEvent, (payload: MovieViewCountPayload) =>
      handlersRef.current.onViewCount?.(payload),
    );
    socket.on(typingEvent, (payload: MovieTypingPayload) =>
      handlersRef.current.onTyping?.(payload),
    );

    return () => {
      socket.off(commentEvent);
      socket.off(ratingEvent);
      socket.off(viewCountEvent);
      socket.off(typingEvent);
      socket.disconnect();
      socketRef.current = null;
    };
  }, [movieId]);
}

/**
 * Gửi sự kiện "đang gõ bình luận" — server broadcast `movie-{id}-typing`
 * cho các client khác.
 */
export function emitTypingComment(
  movieId: number | string,
  isTyping: boolean,
  userFullName?: string,
) {
  getSharedSocket().emit('typingComment', {
    movieId: Number(movieId),
    isTyping,
    userFullName,
  });
}
