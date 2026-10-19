'use client';

import Redirecting from '@/components/loading/redirecting';
import Spining from '@/components/loading/spining';
import { roleUtil } from '@/shared/utils/roleUtil';
import { useAuthStore } from '@/stores/auth.store';
import { usePathname, useRouter } from 'next/navigation';
import React, { useEffect, useState } from 'react';

interface RequireRoleProps {
  requiredRoles: string[];
  children: React.ReactNode;
}

export function ForbiddenPage() {
  return (
    <div className="m-auto text-center text-lg text-red-500">
      Bạn không có quyền truy cập vào trang này.
    </div>
  );
}

export default function RequireRole({ requiredRoles, children }: RequireRoleProps) {
  // loading auth
  const isLoading = useAuthStore((state) => state.isLoading);
  // auth user
  const user = useAuthStore((state) => state.user);
  const router = useRouter();
  const pathname = usePathname();

  // mounted
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // useeffect to redirect to login if user is not authenticated
  useEffect(() => {
    if (!isLoading && !user) {
      router.push(`/auth/login?return-page=${encodeURIComponent(pathname)}`);
    }
  }, [isLoading, user, router]);

  // public
  if (!requiredRoles || requiredRoles.length === 0) {
    return children;
  }

  // unmounted or loading
  if (!isMounted || isLoading) {
    return <Spining />;
  }

  if (!user) {
    return <Redirecting />;
  }

  const userRoleCodes = roleUtil.mapRoleToCodes(user.roles);

  const hasRequiredRole = requiredRoles.some((requiredRole) =>
    userRoleCodes.includes(requiredRole),
  );

  // forbidden
  if (!hasRequiredRole) {
    return <ForbiddenPage />;
  }

  return children;
}
