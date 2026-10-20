import type { Metadata } from 'next';
import { Suspense } from 'react';
import Spining from '@/components/loading/spining';
import { ChatWorkbench } from './chat-workbench';

export const metadata: Metadata = {
  title: 'Hỏi đáp pháp luật',
  description:
    'Đặt câu hỏi pháp luật bằng tiếng Việt và nhận câu trả lời kèm trích dẫn Điều/Khoản/Điểm liên quan.',
};

/**
 * Trang hỏi đáp pháp luật.
 *
 * `ChatWorkbench` đọc `?q=` từ URL nên phải bọc trong `Suspense` (quy ước Next 15+
 * với `useSearchParams`).
 */
export default function ChatPage() {
  return (
    <Suspense fallback={<Spining />}>
      <ChatWorkbench />
    </Suspense>
  );
}
