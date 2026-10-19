'use client';

import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { useRequireLoginStore } from '@/stores/require-login.store';
import { usePathname, useRouter } from 'next/navigation';

/**
 * Hộp thoại thông báo **chưa đăng nhập** khi user bấm các tương tác cần JWT
 * (like/favorite/watchlist/đánh giá/bình luận trên card hoặc chi tiết phim).
 * user xác nhận → chuyển `/auth/login?return-page=<trang hiện tại>`; hủy → ở lại trang.
 * Trạng thái mở/đóng chung qua `useRequireLoginStore` (mount 1 lần trong `UserLayout`).
 */
export function RequireLoginDialog() {
  const router = useRouter();
  const pathname = usePathname();
  const isOpen = useRequireLoginStore((state) => state.isOpen);
  const closeDialog = useRequireLoginStore((state) => state.closeDialog);

  const handleConfirm = () => {
    closeDialog();
    router.push(`/auth/login?return-page=${encodeURIComponent(pathname)}`);
  };

  return (
    <ConfirmDialog
      isOpen={isOpen}
      title="Bạn chưa đăng nhập"
      description="Bạn cần đăng nhập để thực hiện thao tác này. Bạn có muốn chuyển đến trang đăng nhập không?"
      confirmText="Đăng nhập"
      cancelText="Ở lại"
      variant="default"
      onConfirm={handleConfirm}
      onCancel={closeDialog}
    />
  );
}
