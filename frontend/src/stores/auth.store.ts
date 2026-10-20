import { legalAuthApi } from '@/apis/legal.api';
import { LegalUser } from '@/shared/types/legal.types';
import { toast } from 'sonner';
import { create } from 'zustand';

interface AuthState {
  accessToken: string | null;
  user: LegalUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  bootstrap: () => Promise<LegalUser | null>;
  setAccessToken: (token: string | null) => void;
  setUser: (user: LegalUser) => void;
  refreshUser: () => Promise<LegalUser | null>;
  clearAuth: () => void;
  logout: () => Promise<void>;
}

let bootstrapping: Promise<LegalUser | null> | null = null;

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isLoading: true,
  isAuthenticated: false,

  // F5: đọc cookie refreshToken → lấy accessToken mới → gọi /auth/me
  bootstrap: () => {
    bootstrapping ??= (async () => {
      set({ isLoading: true });
      try {
        // Không có phiên hợp lệ (cookie thiếu/hết hạn) cũng là trạng thái bình thường → không toast.
        const refreshResult = await legalAuthApi.refresh();
        if (!refreshResult.success || !refreshResult.result?.accessToken) {
          set({ user: null, isAuthenticated: false });
          return null;
        }
        set({ accessToken: refreshResult.result.accessToken });

        // get me
        const { result: data } = await legalAuthApi.getMe();
        if (!data) {
          set({ user: null, isAuthenticated: false });
          toast.error('Không thể lấy thông tin người dùng. Vui lòng đăng nhập lại.');
          return null;
        }
        set({ user: data });
        set({ isAuthenticated: true });
        return data;
      } catch {
        set({ user: null, isAuthenticated: false });
        return null;
      } finally {
        set({ isLoading: false });
        bootstrapping = null;
      }
    })();
    return bootstrapping;
  },

  setAccessToken: (accessToken) => set({ accessToken }),

  setUser: (user) => set({ user }),

  refreshUser: async () => {
    try {
      const { result: data } = await legalAuthApi.getMe();
      if (!data) {
        set({ user: null, isAuthenticated: false });
        toast.error('Không thể lấy thông tin người dùng. Vui lòng đăng nhập lại.');
        return null;
      }
      set({ user: data });
      set({ isAuthenticated: true });
      return data;
    } catch {
      set({ user: null, isAuthenticated: false });
      return null;
    }
  },

  clearAuth: () =>
    set({
      accessToken: null,
      user: null,
      isLoading: false,
      isAuthenticated: false,
    }),

  logout: async (): Promise<void> => {
    try {
      await legalAuthApi.logout();
    } finally {
      set({
        accessToken: null,
        user: null,
        isLoading: false,
        isAuthenticated: false,
      });
    }
    return Promise.resolve();
  },
}));

/**
 * Helper RBAC dùng chung cho UI mới: kiểm tra người dùng hiện tại có vai trò `admin`.
 * Contract chỉ có 2 vai trò (`user` | `admin`).
 */
export const isAdminUser = (user: LegalUser | null | undefined): boolean => user?.role === 'admin';
