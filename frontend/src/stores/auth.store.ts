import { authApi } from '@/apis/auth.api';
import { User } from '@/shared/types/api.types';
import { toast } from 'sonner';
import { create } from 'zustand';

interface AuthState {
  accessToken: string | null;
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  bootstrap: () => Promise<User | null>;
  setAccessToken: (token: string | null) => void;
  setUser: (user: User) => void;
  refreshUser: () => Promise<User | null>;
  clearAuth: () => void;
  logout: () => Promise<void>;
}

let bootstrapping: Promise<User | null> | null = null;

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isLoading: true,
  isAuthenticated: false,

  // F5 / social callback: refresh → me
  bootstrap: () => {
    bootstrapping ??= (async () => {
      set({ isLoading: true });
      try {
        // refresh token
        const refreshResult = await authApi.refresh();
        if (!refreshResult.success || !refreshResult.result.accessToken) {
          set({ user: null, isAuthenticated: false });
          toast.error('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
          return null;
        }
        set({ accessToken: refreshResult.result.accessToken });

        // get me
        const { result: data } = await authApi.getMe();
        if (!data) {
          set({ user: null, isAuthenticated: false });
          toast.error('Không thể lấy thông tin người dùng. Vui lòng đăng nhập lại.');
          return null;
        }
        set({ user: data });
        set({ isAuthenticated: true });
        return data;
      } catch {
        set({ user: null });
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
      const { result: data } = await authApi.getMe();
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
    await authApi.logout();
    set({
      accessToken: null,
      user: null,
      isLoading: false,
      isAuthenticated: false,
    });
    return Promise.resolve();
  },
}));
