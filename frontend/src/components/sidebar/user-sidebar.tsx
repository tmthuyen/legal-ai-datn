'use client';

import * as React from 'react';

import { UserNavMain } from '@/components/sidebar/nav-main';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from '@/components/ui/sidebar';
import { NavUser } from './nav-user';
import Image from 'next/image';
import Link from 'next/link';

export function UserSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader className="flex h-16 items-start justify-center border-b shadow-sm">
        <Link
          href="/dashboard"
          className="flex min-h-16 w-full items-center justify-start object-cover"
        >
          <Image width={48} height={48} src="/logo2.png" alt="Logo" />
          <h1 className="ml-2 text-lg font-bold text-gray-900 dark:text-white">Movie</h1>
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <UserNavMain />
      </SidebarContent>
      <SidebarFooter className="mb-2">
        <NavUser />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
