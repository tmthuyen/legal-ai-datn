'use client';

import RoleLayout from '@/components/layout/RoleLayout';
import React from 'react';

function MainLayout({ children }: { children: React.ReactNode }) {
  return <RoleLayout>{children}</RoleLayout>;
}

export default MainLayout;
