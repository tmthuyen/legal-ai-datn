import { create } from 'zustand';

interface RequireLoginState {
  isOpen: boolean;
  openDialog: () => void;
  closeDialog: () => void;
}

/**
 * Trạng thái hộp thoại "chưa đăng nhập" — mở bởi `useRequireLogin()` khi guest
 * bấm các tương tác cần JWT (like/favorite/rating/comment…), đóng bởi dialog.
 */
export const useRequireLoginStore = create<RequireLoginState>((set) => ({
  isOpen: false,
  openDialog: () => set({ isOpen: true }),
  closeDialog: () => set({ isOpen: false }),
}));
