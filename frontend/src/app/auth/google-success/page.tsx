'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth.store';
import { roleUtil } from '@/shared/utils/roleUtil';
import { FcGoogle } from 'react-icons/fc';
import { Loader2 } from 'lucide-react';
import { Card } from '@/components/ui/card';

export default function AuthCallbackPage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const isLoading = useAuthStore((state) => state.isLoading);

  useEffect(() => {
    if (user) {
      router.push(roleUtil.getHomeRouteByRole(user.roles));

      return;
    }

    if (!user && !isLoading) {
      router.push('/auth/login?error=google-login-failed');
    }
  }, [router, user]);

  return (
    <div className="gap-2text-lg flex h-screen w-screen items-center justify-center font-semibold">
      <Card className="flex flex-row items-center justify-center gap-4 rounded-2xl border p-4 shadow-lg">
        <Loader2 className="text-primary h-16 w-16 animate-spin" />
        <FcGoogle className="h-8 w-8" />
        <h3 className="text-primary text-lg font-semibold">Đang đăng nhập với Google...</h3>
      </Card>
    </div>
  );
}
