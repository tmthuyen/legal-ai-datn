'use client';

import { usePathname } from 'next/navigation';
import React from 'react';
import AdminLayout from '@/components/layout/AdminLayout';

function MainLayout({ children }: { children: React.ReactNode }) {
  const pathName = usePathname();
  return <AdminLayout>{children}</AdminLayout>;
}

export default MainLayout;
