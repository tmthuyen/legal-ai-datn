'use client';

import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Button } from '@/components/ui/button';
import { ChevronDown, ScrollText, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import { nodeTypeLabel, RelatedNode } from '@/shared/utils/legal';

interface LegalCitationCardProps {
  node: RelatedNode;
  /** Mặc định mở nội dung? (mặc định: mở cho node có text ngắn). */
  defaultOpen?: boolean;
}

/**
 * Thẻ trích dẫn **một** node luật (Điều/Khoản/Điểm…) trả về từ AI.
 * Hiển thị `citation`, `title`, `type`, `number` và `text` (thu gọn/mở rộng được).
 */
export function LegalCitationCard({ node, defaultOpen = false }: LegalCitationCardProps) {
  const [open, setOpen] = useState(defaultOpen);

  const heading = node.citation || node.title || node.nodeId || 'Trích dẫn luật';
  const hasText = !!node.text && node.text.trim().length > 0;
  const hasDetail = hasText || !!node.nodeId;

  return (
    <Card className="gap-0 overflow-hidden py-0">
      <CardHeader className="gap-1 px-4 py-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="flex items-start gap-2">
            <ScrollText className="text-primary mt-0.5 size-4 shrink-0" aria-hidden />
            <div className="flex flex-col gap-1">
              <CardTitle className="text-sm leading-snug">{heading}</CardTitle>
              {node.title && node.title !== heading ? (
                <p className="text-muted-foreground text-xs">{node.title}</p>
              ) : null}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-1">
            <Badge variant="secondary">{nodeTypeLabel(node.type)}</Badge>
            {node.number ? <Badge variant="outline">Số {node.number}</Badge> : null}
          </div>
        </div>
      </CardHeader>

      {hasDetail ? (
        <Collapsible open={open} onOpenChange={setOpen}>
          <CollapsibleContent>
            <CardContent className="px-4 pb-3">
              {hasText ? (
                <p className="text-foreground/90 text-sm leading-relaxed whitespace-pre-line">
                  {node.text}
                </p>
              ) : null}
              {node.nodeId ? (
                <p className="text-muted-foreground mt-3 flex items-center gap-1 text-xs">
                  <ExternalLink className="size-3" aria-hidden />
                  <span className="font-mono">{node.nodeId}</span>
                </p>
              ) : null}
            </CardContent>
          </CollapsibleContent>
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground h-8 w-full justify-center rounded-none border-t text-xs"
            >
              <ChevronDown className={cn('size-3.5 transition-transform', open && 'rotate-180')} />
              {open ? 'Thu gọn nội dung' : 'Xem nội dung'}
            </Button>
          </CollapsibleTrigger>
        </Collapsible>
      ) : null}
    </Card>
  );
}

interface LegalCitationListProps {
  nodes: RelatedNode[];
  className?: string;
}

/** Danh sách thẻ trích dẫn — render khi có `relatedNodes` từ câu trả lời của bot. */
export function LegalCitationList({ nodes, className }: LegalCitationListProps) {
  if (nodes.length === 0) return null;
  return (
    <div className={cn('flex flex-col gap-2', className)}>
      {nodes.map((node, index) => (
        <LegalCitationCard key={node.nodeId ?? `node-${index}`} node={node} />
      ))}
    </div>
  );
}
