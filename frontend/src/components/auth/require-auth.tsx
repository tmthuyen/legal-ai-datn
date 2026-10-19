'use client';

import Redirecting from '@/components/loading/redirecting';
import Spining from '@/components/loading/spining';
import { useAuthStore } from '@/stores/auth.store';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

/**
 * Guard "cần đăng nhập" cho các trang cá nhân (`/my-history`, `/my-favorites`…):
 * - Guest → redirect `/auth/login?return-page=<trang hiện tại>`, không hiện nội dung.
 * - Đang khôi phục phiên / chờ xác nhận user → spinner, tránh "nháy" nội dung.
 *
 * (Khác `RequireRole`: chỉ yêu cầu đăng nhập, không kiểm tra role.)
 */
export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const isLoading = useAuthStore((state) => state.isLoading);
  const user = useAuthStore((state) => state.user);
  const router = useRouter();
  const pathname = usePathname();

  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted || isLoading) return;
    if (!user) {
      router.replace(`/auth/login?return-page=${encodeURIComponent(pathname)}`);
    }
  }, [isMounted, isLoading, user, router, pathname]);

  if (!isMounted || isLoading) {
    return <Spining />;
  }

  if (!user) {
    return <Redirecting />;
  }

  return <>{children}</>;
}
