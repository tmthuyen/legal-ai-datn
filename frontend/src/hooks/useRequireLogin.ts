'use client';

import { useAuthStore } from '@/stores/auth.store';
import { useRequireLoginStore } from '@/stores/require-login.store';
import { useCallback } from 'react';

/**
 * Guard đăng nhập cho các tương tác cần JWT (thích/yêu thích/đánh giá/bình luận…):
 * - Đã đăng nhập → trả `true`, component cho phép thực hiện tiếp.
 * - Chưa đăng nhập → mở **hộp thoại** yêu cầu đăng nhập (không redirect ngay), trả `false`.
 *
 * ```tsx
 * const requireLogin = useRequireLogin();
 * if (!requireLogin()) return; // guest → dialog hiện ra
 * ```
 */
export function useRequireLogin() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const openDialog = useRequireLoginStore((state) => state.openDialog);

  return useCallback((): boolean => {
    if (isAuthenticated) return true;
    openDialog();
    return false;
  }, [isAuthenticated, openDialog]);
}
