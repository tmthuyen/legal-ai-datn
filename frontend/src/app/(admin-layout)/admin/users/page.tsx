import React from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { UsersClient } from './users-client';

export const metadata = {
  title: 'Người dùng',
  description: 'Quản lý người dùng',
};

export default function Page() {
  return (
    <div className="flex h-full w-full flex-col gap-4">
      <PageHeader title={metadata.title} description={metadata.description} />

      {/* content */}
      <UsersClient />
    </div>
  );
}
