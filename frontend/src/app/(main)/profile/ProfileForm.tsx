'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LogOut, Shield, User as UserIcon } from 'lucide-react';
import { useAuthStore } from '@/stores/auth.store';
import { usePathname, useRouter } from 'next/navigation';
import UpdatePasswordForm from '@/app/(main)/profile/UpdatePasswordForm';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import UserProfileForm from '@/app/(main)/profile/UserProfileForm';

/** Shell trang hồ sơ: điều hướng tab (thông tin cá nhân / bảo mật) + đăng xuất. */
export const ProfileForm = () => {
  const user = useAuthStore((state) => state.user);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    useAuthStore.getState().refreshUser();
  }, []);

  useEffect(() => {
    if (!user) {
      router.push('/auth/login?return-page=' + encodeURIComponent(pathname));
    }
  }, [user, router, pathname]);

  const tabs = [
    { label: 'Thông tin cá nhân', value: 'profile', icon: <UserIcon className="h-4 w-4" /> },
    { label: 'Bảo mật', value: 'security', icon: <Shield className="h-4 w-4" /> },
  ];
  const [activeTab, setActiveTab] = useState('profile');

  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const handleLogout = async () => {
    await useAuthStore.getState().logout();
    router.push('/auth/login');
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {/* Cột trái: Navigation */}
      <div className="w-full space-y-6 lg:col-span-1">
        <Card className="w-full gap-4 overflow-hidden border-gray-200 bg-white shadow-lg dark:border-slate-800 dark:bg-slate-900">
          <CardHeader className="bg-white dark:bg-slate-900">
            <div className="flex items-center gap-4">
              {/* Avatar */}
              <Avatar className="h-16 w-16">
                <AvatarImage
                  src={user?.avatarUrl ?? undefined}
                  alt={user?.fullName ?? user?.username ?? 'Người dùng'}
                />
                <AvatarFallback>
                  {(user?.fullName ?? user?.username ?? 'U').charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>

              <div className="min-w-0">
                <h3 className="truncate text-lg font-bold text-gray-900 dark:text-white">
                  {user?.fullName || user?.username || 'Người dùng'}
                </h3>
                <p className="truncate text-sm text-gray-500 dark:text-gray-300">{user?.email}</p>
              </div>
            </div>
          </CardHeader>

          {/* divider */}
          <div className="border-2 border-t border-gray-100 dark:border-slate-800"></div>

          <CardContent className="pt-0">
            <div className="space-y-2">
              {tabs.map((tab) => (
                <Button
                  onClick={() => setActiveTab(tab.value)}
                  key={tab.value}
                  className={`w-full justify-start gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 ${activeTab === tab.value ? 'bg-primary !hover:bg-primary dark:hover:bg-primary' : 'hover:bg-accent bg-white dark:bg-slate-900'}`}
                >
                  {tab.icon}
                  {tab.label}
                </Button>
              ))}
              <Button
                key={'logout'}
                onClick={() => setIsConfirmOpen(true)}
                variant="default"
                className="text-destructive dark:text-destructive-foreground w-full justify-start gap-2 bg-white text-sm font-medium hover:bg-white dark:bg-slate-900 dark:hover:bg-slate-900"
              >
                <LogOut className="h-4 w-4" />
                Đăng xuất
              </Button>
            </div>
          </CardContent>

          <ConfirmDialog
            isOpen={isConfirmOpen}
            title="Đăng xuất"
            description="Bạn có chắc muốn đăng xuất phiên làm việc ?"
            onConfirm={handleLogout}
            onCancel={() => setIsConfirmOpen(false)}
            confirmText="Đăng xuất"
          />
        </Card>
      </div>

      {/* Cột phải: Card */}
      <div className="space-y-6 lg:col-span-2">
        {activeTab === 'profile' && <UserProfileForm />}

        {activeTab === 'security' && <UpdatePasswordForm />}
      </div>
    </div>
  );
};
