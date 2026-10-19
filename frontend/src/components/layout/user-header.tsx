'use client';

import {
  DesktopSearch,
  MobileSearchExpanded,
  MobileSearchToggle,
} from '@/components/layout/header-search';
import { QuickNavDropdown } from '@/components/layout/quick-nav-dropdown';
import { UserMenu } from '@/components/layout/user-menu';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useState } from 'react';

/** Glassmorphism thật: nền trong suốt (`/75`) + `backdrop-blur-md` — blur chỉ có ý nghĩa khi nền không opaque. */
const DEFAULT_HEADER_CLASS =
  'bg-sidebar/75 sticky top-0 right-0 left-0 z-10 flex h-16 shrink-0 items-center border-b px-4 shadow-lg backdrop-blur-md transition-all ease-linear md:px-8';

/**
 * Top header cho khu vực người dùng — dùng trên **cả mobile & desktop**:
 * - Desktop (`md+`): nút mở/tắt sidebar + ô tìm kiếm inline kiểu YouTube.
 * - Mobile: sidebar ẩn; icon tìm kiếm mở rộng thành hàng input (kiểu YouTube);
 *   điều hướng chính qua `MobileBottomNav` + dropdown user tại đây.
 * - Logo/link về trang chủ, toggle theme, dropdown tài khoản (`UserMenu`).
 */
export default function UserHeader({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  /** Trạng thái mở rộng ô tìm kiếm trên mobile (`< md`). */
  const [searchOpen, setSearchOpen] = useState(false);

  // useEffect để tránh hydration mismatch
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  return (
    <header className={className ?? DEFAULT_HEADER_CLASS}>
      {/* Hàng thường — ẩn đi trên mobile khi ô tìm kiếm đang mở rộng */}
      <div
        className={
          searchOpen ? 'hidden w-full md:flex' : 'flex w-full items-center gap-2'
        }
      >
        {/* Mở sidebar (chỉ desktop; mobile dùng bottom nav) */}
        <SidebarTrigger className="hidden shrink-0 cursor-pointer md:inline-flex" />

        {/* Logo + tên website */}
        <Link
          href="/"
          className="flex shrink-0 items-center gap-2 rounded-lg px-1 py-1 transition-opacity hover:opacity-80"
        >
          <Image width={32} height={32} src="/logo2.png" alt="Logo" />
          <span className="text-lg font-bold text-gray-900 dark:text-white">Movie</span>
        </Link>

        {/* Ô tìm kiếm inline (kiểu YouTube) — desktop */}
        <div className="hidden flex-1 justify-center md:flex">
          <DesktopSearch />
        </div>

        <div className="ms-auto flex items-center gap-1 sm:gap-2">
          {/* Icon tìm kiếm (mobile) — mở rộng thành hàng input */}
          <MobileSearchToggle onClick={() => setSearchOpen(true)} />

          {/* Dropdown điều hướng nhanh (route + tính năng) — dùng chung với admin */}
          <QuickNavDropdown variant="user" />

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

          {/* Dropdown tài khoản (route shortcuts, đăng nhập/đăng xuất) */}
          <UserMenu />
        </div>
      </div>

      {/* Hàng tìm kiếm mở rộng (mobile) — thay nguyên hàng header, kiểu YouTube */}
      {searchOpen && (
        <div className="w-full md:hidden">
          <MobileSearchExpanded onClose={() => setSearchOpen(false)} />
        </div>
      )}
    </header>
  );
}
