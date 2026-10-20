/**
 * Kiểu dữ liệu Legal AI — khớp **chính xác** `docs/contracts/API_CONTRACT.md` §3.
 *
 * Nguyên tắc: chỉ khai báo field/kiểu có trong contract; **không** `any` cho dữ liệu API
 * (dùng `unknown` + narrow khi cấu trúc chưa chắc chắn, ví dụ `relatedNodes`).
 */

/** Vai trò người dùng — RBAC của Services chỉ có 2 giá trị. */
export type UserRole = 'user' | 'admin';

/** Người gửi tin nhắn trong hội thoại. */
export type MessageSender = 'user' | 'bot';

/** §3.1 User — thông tin người dùng (không bao giờ chứa `passwordHash`). */
export interface LegalUser {
  id: string;
  email: string;
  username: string;
  fullName: string | null;
  avatarUrl: string | null;
  role: UserRole;
  isActive: boolean;
  /** ISO-8601 UTC. */
  createdAt: string;
  /** ISO-8601 UTC. */
  updatedAt: string;
}

/** §3.2 AuthResult — kết quả đăng nhập/đăng ký. `refreshToken` nằm ở cookie, không trong body. */
export interface AuthResult {
  accessToken: string;
  user: LegalUser;
}

/** §3.3 Conversation — cuộc hội thoại của một user. */
export interface Conversation {
  id: string;
  userId: string;
  title: string;
  /** ISO-8601 UTC. */
  createdAt: string;
  /** ISO-8601 UTC. */
  updatedAt: string;
}

/** §3.4 Message — một tin nhắn trong hội thoại (user hoặc bot). */
export interface Message {
  id: string;
  conversationId: string;
  sender: MessageSender;
  content: string;
  extractedHierarchy: Record<string, unknown> | null;
  relatedNodes: unknown[] | null;
  metadata: Record<string, unknown> | null;
  /** ISO-8601 UTC. */
  createdAt: string;
}

/** §3.5 ChatReply — kết quả 1 lượt hỏi đáp (message user + message bot kèm citations). */
export interface ChatReply {
  userMessage: Message;
  botMessage: Message;
}

/** §4.4 Admin analytics — thống kê tổng quan hệ thống. */
export interface AdminAnalytics {
  totalUsers: number;
  totalConversations: number;
  totalQuestions: number;
}

/** §4.1 Auth — body đăng nhập. */
export interface LoginPayload {
  username: string;
  password: string;
}

/** §4.1 Auth — body đăng ký. `fullName` tùy chọn. */
export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
  fullName?: string;
}

/** §4.2 User — body cập nhật hồ sơ (ít nhất 1 trường). */
export interface UpdateProfilePayload {
  fullName?: string;
  avatarUrl?: string;
}

/** §4.2 User — body đổi mật khẩu. */
export interface UpdatePasswordPayload {
  oldPassword: string;
  newPassword: string;
}

/** §4.3 Chat — body tạo hội thoại (`title` tùy chọn). */
export interface CreateConversationPayload {
  title?: string;
}

/** §4.3 Chat — body gửi câu hỏi. */
export interface SendMessagePayload {
  content: string;
}

/** §4.4 Admin — body khóa/mở khóa tài khoản. */
export interface UpdateUserStatusPayload {
  isActive: boolean;
}
