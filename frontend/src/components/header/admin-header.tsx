'use client';

import { useEffect, useState } from 'react';
import { useTheme } from 'next-themes';
import Link from 'next/link';
import Image from 'next/image';
import { Home, Moon, Sun } from 'lucide-react';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { QuickNavDropdown } from '@/components/layout/quick-nav-dropdown';
import { UserMenu } from '@/components/layout/user-menu';

/**
 * Top header khu vực admin — dùng trên cả mobile & desktop:
 * - Nút mở/tắt sidebar (desktop) + logo/tên khu vực quản trị.
 * - Dropdown **điều hướng nhanh** (`QuickNavDropdown`, shadcn `DropdownMenu`) để nhảy
 *   route quản trị nhanh; nút về trang người dùng; toggle theme; dropdown tài khoản (`UserMenu`).
 */
function AdminHeader({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // useEffect để tránh hydration mismatch
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  return (
    <header className={className}>
      <div className="flex w-full items-center gap-2 md:gap-4">
        <SidebarTrigger className="-ml-1 shrink-0 cursor-pointer" />

        <Link
          href="/dashboard"
          className="flex shrink-0 items-center gap-2 rounded-lg px-1 py-1 transition-opacity hover:opacity-80"
        >
          <Image width={32} height={32} src="/logo2.png" alt="Logo" />
          <span className="text-lg font-bold text-gray-900 dark:text-white">Admin</span>
        </Link>

        <div className="ms-auto flex items-center gap-1 sm:gap-2">
          {/* Dropdown điều hướng nhanh (route + tính năng quản trị) */}
          <QuickNavDropdown variant="admin" />

          {/* Về trang người dùng */}
          <Link
            href="/"
            title="Xem trang người dùng"
            aria-label="Xem trang người dùng"
            className="cursor-pointer rounded-full p-2 text-gray-600 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-slate-800"
          >
            <Home className="size-5" aria-hidden="true" />
          </Link>

          {/* Toggle theme */}
          <button
            type="button"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="cursor-pointer rounded-full p-2 text-gray-600 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-slate-800"
            title="Đổi giao diện Sáng/Tối"
            aria-label="Đổi giao diện Sáng/Tối"
          >
            {!mounted ? (
              <div className="h-5 w-5 animate-pulse rounded-full bg-gray-200 dark:bg-gray-700" />
            ) : theme === 'dark' ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </button>

          {/* Dropdown tài khoản (hồ sơ, dashboard, đăng xuất) */}
          <UserMenu />
        </div>
      </div>
    </header>
  );
}

export default AdminHeader;
