'use client';

import { AdminSidebar } from '@/components/sidebar/admin-sidebar';
import Header from '@/components/header/admin-header';
import { AdminMobileBottomNav } from '@/components/layout/mobile-bottom-nav';
import { SiteFooter } from '@/components/layout/site-footer';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import React from 'react';
import RequireRole from '@/components/auth/RequireRole';

/**
 * Shell khu vực admin (chỉ vai trò `ADMIN`):
 * - Sidebar desktop (`md+`); mobile ẩn, điều hướng qua `AdminMobileBottomNav` + dropdown header.
 * - Content wrapper là **block** (`min-w-0`) để bảng/biểu đồ rộng cuộn trong khung của nó,
 *   không đẩy ra ngoài gây scroll ngang toàn trang (giống `UserLayout`).
 * - Footer dùng chung `SiteFooter`; `pb-16 md:pb-0` chừa chỗ bottom nav trên mobile.
 */
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireRole requiredRoles={['ADMIN']}>
      <div className="flex min-h-screen w-full">
        <SidebarProvider>
          <AdminSidebar />
          <SidebarInset className="min-w-0 bg-slate-50 pb-16 text-slate-900 transition-colors duration-300 dark:bg-slate-950 dark:text-zinc-50 md:pb-0">
            <Header className="bg-sidebar/75 sticky top-0 right-0 left-0 z-10 flex h-16 shrink-0 items-center border-b px-4 shadow-lg backdrop-blur-md transition-all ease-linear md:px-8" />

            <div className="mx-auto w-full max-w-7xl min-w-0 flex-1 px-4 pt-4 md:px-8 md:pt-8">
              {children}
            </div>

            <SiteFooter />
          </SidebarInset>
          <AdminMobileBottomNav />
        </SidebarProvider>
      </div>
    </RequireRole>
  );
}
