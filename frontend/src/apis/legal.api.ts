import axiosClient from '@/lib/axiosClient';
import {
  AdminAnalytics,
  AuthResult,
  ChatReply,
  Conversation,
  CreateConversationPayload,
  LegalUser,
  LoginPayload,
  Message,
  RegisterPayload,
  SendMessagePayload,
  UpdatePasswordPayload,
  UpdateProfilePayload,
  UpdateUserStatusPayload,
} from '@/shared/types/legal.types';
import { ApiPaginatedResponse, ApiResponse } from '@/shared/types/api.types';

/**
 * Lớp gọi API Legal AI — bọc **đúng** endpoint trong `docs/contracts/API_CONTRACT.md` §4,
 * dùng lại `axiosClient` (interceptor gắn Bearer + refresh 401 + `keysToCamel`).
 *
 * Quy ước: mọi hàm trả về nguyên envelope (`ApiResponse<T>` / `ApiPaginatedResponse<T>`)
 * để tầng hook đọc `result`/`message`/`pagination` thống nhất; lỗi để `axios` ném ra và
 * tầng UI parse bằng `parseAxiosError`.
 */

/** §4.1 Auth — đăng ký, đăng nhập, refresh, logout, me. */
export const legalAuthApi = {
  /** `POST /auth/register` — 201. `result`: `AuthResult` + set cookie `refreshToken`. */
  register: async (payload: RegisterPayload): Promise<ApiResponse<AuthResult>> => {
    const { data } = await axiosClient.post('/auth/register', payload);
    return data;
  },

  /** `POST /auth/login` — 200. `result`: `AuthResult` + set cookie `refreshToken`. */
  login: async (payload: LoginPayload): Promise<ApiResponse<AuthResult>> => {
    const { data } = await axiosClient.post('/auth/login', payload);
    return data;
  },

  /**
   * `POST /auth/refresh` — 200. Không body; đọc cookie `refreshToken`.
   * `result`: `{ accessToken }` (refresh token không nằm trong body).
   */
  refresh: async (): Promise<ApiResponse<{ accessToken: string }>> => {
    const { data } = await axiosClient.post('/auth/refresh', null, { withCredentials: true });
    return data;
  },

  /** `POST /auth/logout` — 200. Xóa cookie `refreshToken`. `result`: `null`. */
  logout: async (): Promise<ApiResponse<null>> => {
    const { data } = await axiosClient.post('/auth/logout');
    return data;
  },

  /** `GET /auth/me` — 200. Cần Bearer. `result`: `LegalUser`. */
  getMe: async (): Promise<ApiResponse<LegalUser>> => {
    const { data } = await axiosClient.get('/auth/me');
    return data;
  },
};

/** §4.2 User / Profile. */
export const legalUserApi = {
  /** `PUT /user/profile` — 200. Cần Bearer. `result`: `LegalUser`. */
  updateProfile: async (payload: UpdateProfilePayload): Promise<ApiResponse<LegalUser>> => {
    const { data } = await axiosClient.put('/user/profile', payload);
    return data;
  },

  /** `PUT /user/password` — 200. Cần Bearer. `result`: `null`. */
  updatePassword: async (payload: UpdatePasswordPayload): Promise<ApiResponse<null>> => {
    const { data } = await axiosClient.put('/user/password', payload);
    return data;
  },
};

/** §4.3 Chat & AI Gateway. */
export const legalChatApi = {
  /** `GET /chat/conversations` — 200. Cần Bearer. `Paginated<Conversation>` (`updatedAt` giảm dần). */
  getConversations: async (params?: {
    page?: number;
    limit?: number;
  }): Promise<ApiPaginatedResponse<Conversation[]>> => {
    const { data } = await axiosClient.get('/chat/conversations', { params });
    return data;
  },

  /** `POST /chat/conversations` — 201. Cần Bearer. `result`: `Conversation`. */
  createConversation: async (
    payload: CreateConversationPayload,
  ): Promise<ApiResponse<Conversation>> => {
    const { data } = await axiosClient.post('/chat/conversations', payload);
    return data;
  },

  /** `DELETE /chat/conversations/:id` — 200. Cần Bearer (chỉ chủ sở hữu). `result`: `null`. */
  deleteConversation: async (id: string): Promise<ApiResponse<null>> => {
    const { data } = await axiosClient.delete(`/chat/conversations/${id}`);
    return data;
  },

  /** `GET /chat/conversations/:id/messages` — 200. Cần Bearer. `Paginated<Message>` (`createdAt` tăng dần). */
  getMessages: async (
    id: string,
    params?: { page?: number; limit?: number },
  ): Promise<ApiPaginatedResponse<Message[]>> => {
    const { data } = await axiosClient.get(`/chat/conversations/${id}/messages`, { params });
    return data;
  },

  /** `POST /chat/conversations/:id/messages` — 201. Cần Bearer. `result`: `ChatReply`. */
  sendMessage: async (id: string, payload: SendMessagePayload): Promise<ApiResponse<ChatReply>> => {
    const { data } = await axiosClient.post(`/chat/conversations/${id}/messages`, payload);
    return data;
  },
};

/** §4.4 Admin (role `admin`, ngược lại `403`). */
export const legalAdminApi = {
  /** `GET /admin/users` — 200. Query `page`, `limit`, `search`. `Paginated<LegalUser>`. */
  getUsers: async (params?: {
    page?: number;
    limit?: number;
    search?: string;
  }): Promise<ApiPaginatedResponse<LegalUser[]>> => {
    const { data } = await axiosClient.get('/admin/users', { params });
    return data;
  },

  /** `PUT /admin/users/:id/status` — 200. `result`: `LegalUser`. */
  updateUserStatus: async (
    id: string,
    payload: UpdateUserStatusPayload,
  ): Promise<ApiResponse<LegalUser>> => {
    const { data } = await axiosClient.put(`/admin/users/${id}/status`, payload);
    return data;
  },

  /** `GET /admin/analytics` — 200. `result`: `AdminAnalytics`. */
  getAnalytics: async (): Promise<ApiResponse<AdminAnalytics>> => {
    const { data } = await axiosClient.get('/admin/analytics');
    return data;
  },
};

/** Alias gộp — cho phép `import { legalApi } from '@/apis/legal.api'`. */
export const legalApi = {
  auth: legalAuthApi,
  user: legalUserApi,
  chat: legalChatApi,
  admin: legalAdminApi,
};
