import React from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { DashboardClient } from './dashboard-client';

export const metadata = {
  title: 'Tổng quan',
  description: 'Thống kê tổng quan hệ thống Legal AI',
};

/** Trang tổng quan quản trị — thống kê người dùng, hội thoại và số câu hỏi. */
export default function Page() {
  return (
    <div className="flex h-full w-full flex-col gap-4">
      <PageHeader title={metadata.title} description={metadata.description} />

      <DashboardClient />
    </div>
  );
}
