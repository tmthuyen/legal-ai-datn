'use client';

import AdminLayout from '@/components/layout/AdminLayout';
import UserLayout from '@/components/layout/UserLayout';
import Spining from '@/components/loading/spining';
import { roleUtil } from '@/shared/utils/roleUtil';
import { useAuthStore } from '@/stores/auth.store';

export default function RoleLayout({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((state) => state.user);
  const isLoading = useAuthStore((state) => state.isLoading);

  // Đang khôi phục phiên đăng nhập: chờ để tránh "nháy" sai layout.
  if (isLoading) {
    return <Spining />;
  }

  // Guest: vẫn xem được các trang công khai trong (main) với layout người dùng.
  if (!user) {
    return <UserLayout>{children}</UserLayout>;
  }

  const userRoleCodes = roleUtil.mapRoleToCodes(user.roles);

  if (userRoleCodes.includes('ADMIN')) {
    return <AdminLayout>{children}</AdminLayout>;
  }

  return <UserLayout>{children}</UserLayout>;
}
