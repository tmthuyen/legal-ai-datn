'use client';

import { NAV_SECTIONS, NavSectionKey } from '@/components/sidebar/nav-data';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/auth.store';
import { Globe, LayoutGrid } from 'lucide-react';
import Link from 'next/link';

export type QuickNavVariant = 'user' | 'admin';

/** Nhóm nav hiển thị trong dropdown, lấy từ `NAV_SECTIONS` (một nguồn dữ liệu duy nhất). */
const QUICK_NAV_SECTIONS: Record<QuickNavVariant, NavSectionKey[]> = {
  user: ['user', 'personal', 'settings'],
  admin: ['learning', 'auth', 'admin', 'interaction'],
};

/** Nhóm chỉ dành cho người đã đăng nhập. */
const AUTH_ONLY_SECTIONS: NavSectionKey[] = ['personal', 'settings'];

/**
 * Dropdown **điều hướng nhanh** trên header (shadcn `DropdownMenu`): nhảy route và
 * truy cập tính năng nhanh mà không cần mở sidebar. Dùng chung cho user (`variant="user"`)
 * và admin (`variant="admin"`); item lấy từ `NAV_SECTIONS`.
 *
 * Guest chỉ thấy nhóm công khai; admin có thêm lối tắt về trang người dùng.
 */
export function QuickNavDropdown({
  variant = 'user',
  className,
}: {
  variant?: QuickNavVariant;
  className?: string;
}) {
  const user = useAuthStore((state) => state.user);

  const sectionKeys = QUICK_NAV_SECTIONS[variant].filter(
    (key) => variant === 'admin' || user !== null || !AUTH_ONLY_SECTIONS.includes(key),
  );

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Điều hướng nhanh"
          title="Điều hướng nhanh"
          className={cn(
            'cursor-pointer rounded-full p-2 text-gray-600 outline-none transition-colors ring-ring hover:bg-gray-100 focus-visible:ring-2 dark:text-gray-300 dark:hover:bg-slate-800',
            className,
          )}
        >
          <LayoutGrid className="size-5" aria-hidden="true" />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="min-w-56 rounded-lg">
        <DropdownMenuLabel className="text-muted-foreground text-xs font-medium">
          {variant === 'admin' ? 'Quản trị nhanh' : 'Điều hướng nhanh'}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {sectionKeys.map((key) => (
          <DropdownMenuGroup key={key}>
            <DropdownMenuLabel className="text-muted-foreground text-[11px] tracking-wide uppercase">
              {NAV_SECTIONS[key].groupLabel}
            </DropdownMenuLabel>
            {NAV_SECTIONS[key].items.map((item) => (
              <DropdownMenuItem key={item.url} asChild className="cursor-pointer">
                <Link href={item.url}>
                  <item.icon className="mr-2 h-4 w-4" aria-hidden="true" />
                  {item.title}
                </Link>
              </DropdownMenuItem>
            ))}
          </DropdownMenuGroup>
        ))}

        {variant === 'admin' && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild className="cursor-pointer">
              <Link href="/">
                <Globe className="mr-2 h-4 w-4" aria-hidden="true" />
                Xem trang người dùng
              </Link>
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
