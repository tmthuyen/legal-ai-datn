'use client';

import React, { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Laptop,
  Smartphone,
  KeyRound,
  Shield,
  LogOut,
  CheckCircle2,
  User as UserIcon,
  Mail,
  Camera,
  Loader2,
  MapPin,
  Clock,
  PlusIcon,
  LogIn,
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Skeleton } from '@/components/ui/skeleton';
import { userApi } from '@/apis/user.api';
import { authApi } from '@/apis/auth.api';
import { useAuthStore } from '@/stores/auth.store';
import { Role } from '@/shared/types/api.types';
import { mapUserStatus } from '@/shared/utils/mapStatus';
import { usePathname, useRouter } from 'next/navigation';
import { parseAxiosError } from '@/lib/axiosClient';
import UpdatePasswordForm from '@/app/(main)/profile/UpdatePasswordForm';
import dateTimeUtils from '@/shared/utils/formatting';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { Avatar, AvatarBadge, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import UserProfileForm from '@/app/(main)/profile/UserProfileForm';

// props
interface ProfileFormProps {
  metadata: {
    title: string;
    description: string;
  };
  children?: React.ReactNode;
}

export const ProfileForm = ({ metadata, children }: ProfileFormProps) => {
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
  }, [user, router]);

  const tabs = [
    { label: 'Thông tin cá nhân', value: 'profile', icon: <UserIcon className="h-4 w-4" /> },
    { label: 'Bảo mật', value: 'security', icon: <Shield className="h-4 w-4" /> },
    { label: 'Phiên đăng nhập', value: 'sessions', icon: <LogIn className="h-4 w-4" /> },
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
                  src={user?.avatarUrl || 'https://github.com/shadcn.png'}
                  alt={user?.fullName || '@shadcn'}
                />
                <AvatarFallback>{user?.fullName?.charAt(0) || 'U'}</AvatarFallback>
              </Avatar>

              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                  {user?.fullName || 'Người dùng ẩn danh'}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-300">{user?.email}</p>
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
            description="Bạn có chắc muốn đăng xuất phiên làm việc  ?"
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

        {activeTab === 'sessions' && <UserSession />}
      </div>
    </div>
  );
};

export const UserSession = () => {
  const queryClient = useQueryClient();

  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [sessionToRevoke, setSessionToRevoke] = useState<string | null>(null);

  const { data: sessionsData, isLoading: isLoadingSessions } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => authApi.getSessions(),
    staleTime: 3 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });

  const sessions = React.useMemo(() => {
    if (!sessionsData?.result) return [];
    return sessionsData.result.reduce((acc: any[], session: any) => {
      const existingSession = acc.find((s) => s.userAgent === session.userAgent);
      if (!existingSession || !session.isRevoked) {
        acc.push(session);
      }
      return acc;
    }, []);
  }, [sessionsData]);
  const handleRevokeSession = (sessionId: string) => {
    setSessionToRevoke(sessionId);
    setIsConfirmOpen(true);
  };

  const revokeSessionMutation = useMutation({
    mutationFn: (sessionId: string) => authApi.logoutBySession({ sessionId }),
    onSuccess: () => {
      toast.success('Đăng xuất phiên thành công');
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
    onError: (error) => {
      const axiosError = parseAxiosError(error, 'Lỗi khi đăng xuất phiên');
      toast.error(axiosError.message);
    },
  });

  const confirmRevoke = () => {
    if (sessionToRevoke !== null) {
      revokeSessionMutation.mutate(sessionToRevoke);
      setSessionToRevoke(null);
    }
    setIsConfirmOpen(false);
  };
  return (
    <div>
      <Card className="border border-gray-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <CardHeader className="bg-white pb-4 dark:bg-slate-900">
          <CardTitle className="flex items-center gap-2">
            <Shield className={`text-accent-foreground h-5 w-5`} /> Phiên Đăng Nhập
          </CardTitle>
          <CardDescription>
            Quản lý các thiết bị đang đăng nhập vào tài khoản của bạn.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingSessions ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-4 py-4">
                  <Skeleton className="h-12 w-12 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-3 w-1/3" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-slate-800">
              {sessions.length === 0 && (
                <p className="py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                  Không có phiên đăng nhập nào.
                </p>
              )}
              {sessions.map((session: any) => (
                <div key={session.sessionId} className="flex items-center justify-between py-4">
                  <div className="flex items-center gap-4">
                    <div
                      className={`rounded-full p-3 ${!session.isRevoked ? `text-primary/50` : 'bg-gray-100 text-gray-500 dark:bg-slate-900'}`}
                    >
                      {session.userAgent.includes('Mobile') ? (
                        <Smartphone className="h-8 w-8" />
                      ) : (
                        <Laptop className="h-8 w-8" />
                      )}
                    </div>
                    <div className="flex flex-col gap-2">
                      <p className="flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
                        {session.userAgent}
                      </p>
                      <p className="flex items-center gap-2 text-sm text-gray-500">
                        <MapPin className="h-4 w-4" />
                        <span>{session.ip}</span>
                      </p>
                      <p
                        className={`flex items-center gap-2 text-sm ${session.isCurrentSession ? 'text-green-400' : 'text-gray-500'}`}
                      >
                        <Clock className="h-4 w-4" />{' '}
                        <span>{dateTimeUtils.formatDateTime(session.createdAt)}</span>
                        <span className="">
                          {session.isCurrentSession && ' (Thiết bị hiện tại)'}
                        </span>
                      </p>
                    </div>
                  </div>
                  {!session.isRevoked && !session.isCurrentSession && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRevokeSession(session.sessionId)}
                      className="text-red-500 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-900/20"
                      title="Đăng xuất thiết bị này"
                    >
                      <LogOut className="h-5 w-5" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog
        isOpen={isConfirmOpen}
        title="Đăng xuất thiết bị"
        description="Bạn có chắc muốn đăng xuất khỏi thiết bị này?"
        onConfirm={confirmRevoke}
        onCancel={() => setIsConfirmOpen(false)}
        confirmText="Đăng xuất"
      />
    </div>
  );
};
