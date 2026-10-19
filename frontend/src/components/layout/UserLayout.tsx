'use client';

import { RequireLoginDialog } from '@/components/auth/require-login-dialog';
import { MobileBottomNav } from '@/components/layout/mobile-bottom-nav';
import { SiteFooter } from '@/components/layout/site-footer';
import UserHeader from '@/components/layout/user-header';
import { UserSidebar } from '@/components/sidebar/user-sidebar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import React from 'react';

/**
 * Shell cho khu vực người dùng:
 * - Sidebar desktop (`md+`); mobile ẩn, điều hướng qua `MobileBottomNav` + header dropdown.
 * - Content wrapper là **block** (`min-w-0`, không flex) để overflow nội bộ từng trang
 *   (vd. hàng `MovieRow` cuộn ngang) không bị đẩy ra ngoài gây scroll ngang toàn trang.
 * - `SidebarInset` có `pb-16 md:pb-0` chừa chỗ bottom nav trên mobile.
 */
export default function UserLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <UserSidebar />
      <SidebarInset className="min-w-0 bg-slate-50 pb-16 text-slate-900 transition-colors duration-300 dark:bg-slate-950 dark:text-zinc-50 md:pb-0">
        <UserHeader />

        <div className="mx-auto w-full max-w-7xl flex-1 px-4 pt-4 min-w-0 md:px-8 md:pt-8">
          {children}
        </div>

        <SiteFooter />
      </SidebarInset>
      <MobileBottomNav />
      {/* Hộp thoại "chưa đăng nhập" khi guest bấm tương tác cần JWT */}
      <RequireLoginDialog />
    </SidebarProvider>
  );
}
