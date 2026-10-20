import type { Metadata } from 'next';
import { ConversationsClient } from './conversations-client';

export const metadata: Metadata = {
  title: 'Hội thoại của tôi',
  description: 'Quản lý các cuộc hội thoại hỏi đáp pháp luật và xem lại lịch sử câu hỏi.',
};

/** Trang quản lý hội thoại (danh sách phân trang, tạo mới, xóa, xem lịch sử). */
export default function ConversationsPage() {
  return <ConversationsClient />;
}
