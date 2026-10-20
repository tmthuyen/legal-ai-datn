'use client';

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Message } from '@/shared/types/legal.types';
import { toHierarchyEntries, toRelatedNodes } from '@/shared/utils/legal';
import dateTimeUtils from '@/shared/utils/formatting';
import { Bot, User as UserIcon } from 'lucide-react';
import { LegalCitationList } from '@/components/legal/legal-citation';
import { LegalHierarchyBreadcrumb } from '@/components/legal/legal-hierarchy-breadcrumb';

interface ChatMessageBubbleProps {
  message: Message;
  /** Nội dung đang chờ (đang gửi) — hiển thị con trỏ. */
  pending?: boolean;
}

/** Metadata `responseTimeMs` do Services lưu trong `metadata` (contract §4.3). */
function getResponseTimeMs(message: Message): number | null {
  const value = message.metadata?.responseTimeMs;
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

/**
 * Một bong bóng tin nhắn trong khung chat hỏi đáp pháp luật.
 * Với tin nhắn của bot: hiển thị phân cấp luật (`extractedHierarchy`) và thẻ trích dẫn
 * (`relatedNodes`) — trọng tâm giao diện pháp lý.
 */
export function ChatMessageBubble({ message, pending = false }: ChatMessageBubbleProps) {
  const isBot = message.sender === 'bot';
  const nodes = isBot ? toRelatedNodes(message.relatedNodes) : [];
  const hierarchy = isBot ? toHierarchyEntries(message.extractedHierarchy) : [];
  const responseTimeMs = getResponseTimeMs(message);

  return (
    <div className={cn('flex w-full gap-3', isBot ? 'justify-start' : 'justify-end')}>
      {isBot ? (
        <div className="bg-primary/10 text-primary flex size-8 shrink-0 items-center justify-center rounded-full">
          <Bot className="size-4" aria-hidden />
        </div>
      ) : null}

      <div className={cn('flex min-w-0 max-w-[85%] flex-col gap-2', !isBot && 'items-end')}>
        <div
          className={cn(
            'rounded-2xl border px-4 py-2.5 text-sm leading-relaxed',
            isBot
              ? 'bg-card text-card-foreground rounded-tl-sm'
              : 'bg-primary text-primary-foreground border-primary rounded-tr-sm',
          )}
        >
          <p className="whitespace-pre-line">{message.content}</p>
          {pending ? <span className="animate-pulse">▍</span> : null}
        </div>

        {/* Phân cấp luật trích xuất (breadcrumb) — chỉ bot */}
        {isBot && hierarchy.length > 0 ? (
          <div className="bg-muted/60 w-full rounded-lg border px-3 py-2">
            <p className="text-muted-foreground mb-1 text-xs font-medium">Phân cấp luật trích xuất</p>
            <LegalHierarchyBreadcrumb entries={hierarchy} />
          </div>
        ) : null}

        {/* Thẻ trích dẫn Điều/Khoản/Điểm — chỉ bot */}
        {isBot && nodes.length > 0 ? (
          <div className="w-full">
            <p className="text-muted-foreground mb-1 flex items-center gap-2 text-xs font-medium">
              Điều luật liên quan
              <Badge variant="secondary">{nodes.length}</Badge>
            </p>
            <LegalCitationList nodes={nodes} />
          </div>
        ) : null}

        <div className="text-muted-foreground flex items-center gap-2 px-1 text-[11px]">
          {isBot ? (
            <Bot className="size-3" aria-hidden />
          ) : (
            <UserIcon className="size-3" aria-hidden />
          )}
          <span>{isBot ? 'Trợ lý Legal AI' : 'Bạn'}</span>
          <span aria-hidden>•</span>
          <span>{dateTimeUtils.formatDateTime(message.createdAt)}</span>
          {responseTimeMs !== null ? (
            <>
              <span aria-hidden>•</span>
              <span>{(responseTimeMs / 1000).toFixed(2)}s</span>
            </>
          ) : null}
        </div>
      </div>

      {!isBot ? (
        <div className="bg-secondary text-secondary-foreground flex size-8 shrink-0 items-center justify-center rounded-full">
          <UserIcon className="size-4" aria-hidden />
        </div>
      ) : null}
    </div>
  );
}
