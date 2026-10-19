'use client';

import { BOTTOM_NAV, BottomNavItemData } from '@/components/sidebar/nav-data';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/auth.store';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

function isActivePath(pathname: string, item: BottomNavItemData) {
  if (item.exact) return pathname === item.href;
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}

function BottomNavButton({ item, pathname }: { item: BottomNavItemData; pathname: string }) {
  const active = isActivePath(pathname, item);
  return (
    <Link
      href={item.href}
      aria-current={active ? 'page' : undefined}
      className={cn(
        'flex min-w-0 flex-1 flex-col items-center gap-0.5 px-1 py-2 text-[11px] transition-colors',
        active ? 'text-primary font-medium' : 'text-muted-foreground hover:text-foreground',
      )}
    >
      <item.icon className={cn('size-5', active && 'text-primary')} aria-hidden="true" />
      <span className="truncate">{item.label}</span>
    </Link>
  );
}

/** Khung bottom nav dùng chung (user & admin) — cố định đáy, chừa safe-area. */
function BottomNav({ items, ariaLabel }: { items: BottomNavItemData[]; ariaLabel: string }) {
  const pathname = usePathname();

  if (items.length === 0) return null;

  return (
    <nav
      aria-label={ariaLabel}
      className="bg-background/95 fixed right-0 bottom-0 left-0 z-40 border-t shadow-lg backdrop-blur-md md:hidden"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <div className="mx-auto flex w-full max-w-md items-stretch">
        {items.map((item) => (
          <BottomNavButton key={item.href} item={item} pathname={pathname} />
        ))}
      </div>
    </nav>
  );
}

/**
 * Bottom navigation cho khu vực **người dùng** trên màn hình nhỏ (`< md`) — thay cho
 * sidebar (mobile chỉ mở tay qua Sheet). Item lấy từ `BOTTOM_NAV.user`, lọc theo đăng nhập.
 */
export function MobileBottomNav() {
  const user = useAuthStore((state) => state.user);

  const items = BOTTOM_NAV.user.filter((item) =>
    item.guestOnly ? !user : item.requiresAuth ? !!user : true,
  );

  return <BottomNav items={items} ariaLabel="Điều hướng chính" />;
}

/**
 * Bottom navigation cho khu vực **admin** trên màn hình nhỏ (`< md`) — lối tắt tới
 * các trang quản trị thường dùng (Dashboard/Phim/Tương tác/Tài khoản).
 * Item lấy từ `BOTTOM_NAV.admin`.
 */
export function AdminMobileBottomNav() {
  return <BottomNav items={BOTTOM_NAV.admin} ariaLabel="Điều hướng quản trị" />;
}
