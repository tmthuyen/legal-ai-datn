'use client';

import Link from 'next/link';
import { ContactRound, MessagesSquare, MessageSquareText } from 'lucide-react';
import { ErrorState } from '@/components/common/ErrorState';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useAdminAnalytics } from '@/hooks/tankstack/useAdminAnalytics';
import type { LucideIcon } from 'lucide-react';

/** Một ô thống kê (nhãn + giá trị + icon) theo `AdminAnalytics`. */
interface StatCard {
  key: string;
  label: string;
  icon: LucideIcon;
  value: number;
}

/**
 * Dashboard quản trị — đọc `GET /admin/analytics` (`totalUsers`, `totalConversations`,
 * `totalQuestions`) và hiển thị 3 thẻ thống kê. Endpoint yêu cầu role `admin`.
 */
export function DashboardClient() {
  const analytics = useAdminAnalytics();

  if (analytics.isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map((index) => (
          <Skeleton key={index} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  if (analytics.isError || !analytics.data) {
    return (
      <ErrorState
        title="Không thể tải thống kê"
        description="Vui lòng kiểm tra kết nối tới dịch vụ và thử lại."
        onRetry={() => analytics.refetch()}
      />
    );
  }

  const stats: StatCard[] = [
    { key: 'users', label: 'Người dùng', icon: ContactRound, value: analytics.data.totalUsers },
    {
      key: 'conversations',
      label: 'Hội thoại',
      icon: MessagesSquare,
      value: analytics.data.totalConversations,
    },
    {
      key: 'questions',
      label: 'Câu hỏi',
      icon: MessageSquareText,
      value: analytics.data.totalQuestions,
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat) => (
          <Card key={stat.key}>
            <CardHeader className="flex flex-row items-center justify-between gap-2 pb-2">
              <CardTitle className="text-muted-foreground text-sm font-medium">
                {stat.label}
              </CardTitle>
              <div className="bg-primary/10 text-primary flex size-9 items-center justify-center rounded-lg">
                <stat.icon className="size-4" aria-hidden />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{stat.value.toLocaleString('vi-VN')}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Quản lý nhanh</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Link
            href="/admin/users"
            className="bg-muted/60 hover:bg-muted rounded-lg border px-4 py-2 text-sm font-medium transition-colors"
          >
            Quản lý người dùng
          </Link>
          <Link
            href="/chat"
            className="bg-muted/60 hover:bg-muted rounded-lg border px-4 py-2 text-sm font-medium transition-colors"
          >
            Thử hỏi đáp pháp luật
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
