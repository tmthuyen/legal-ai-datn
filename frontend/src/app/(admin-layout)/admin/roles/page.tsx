import React from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { RolesClient } from './roles-client';

export const metadata = {
  title: 'Vai trò',
  description: 'Quản lý vai trò và phân quyền',
};

export default function Page() {
  return (
    <div className="flex h-full w-full flex-col gap-4">
      <PageHeader title={metadata.title} description={metadata.description} />

      {/* content */}
      <RolesClient />
    </div>
  );
}
