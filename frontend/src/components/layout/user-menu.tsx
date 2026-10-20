'use client';

import {
  ChevronsUpDown,
  LayoutDashboard,
  LogIn,
  LogOut,
  MessagesSquare,
  Scale,
  User as UserIcon,
} from 'lucide-react';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { roleUtil } from '@/shared/utils/roleUtil';
import { useAuthStore } from '@/stores/auth.store';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { ComponentProps } from 'react';

/**
 * Dropdown nội dung tài khoản dùng chung cho header (`UserMenu`) và sidebar (`NavUser`).
 * Guest hiển thị 1 nút Đăng nhập; đã đăng nhập hiển thị info + route shortcuts + Đăng xuất.
 */
export function UserMenuContent({
  side = 'bottom',
  align = 'end',
  ...props
}: ComponentProps<typeof DropdownMenuContent>) {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);

  const handleLogout = async () => {
    await useAuthStore.getState().logout();
    router.push('/auth/login');
  };

  if (!user) {
    return (
      <DropdownMenuContent align={align} side={side} {...props}>
        <DropdownMenuItem asChild className="cursor-pointer">
          <Link href="/auth/login">
            <LogIn className="mr-2 h-4 w-4" />
            Đăng nhập
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    );
  }

  const isAdmin = roleUtil.isAdmin(user);

  return (
    <DropdownMenuContent align={align} side={side} {...props}>
      <DropdownMenuLabel className="p-0 font-normal">
        <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
          <Avatar className="h-8 w-8 rounded-lg">
            <AvatarImage src={user.avatarUrl ?? undefined} alt={user.fullName ?? user.username} />
            <AvatarFallback className="rounded-lg">CN</AvatarFallback>
          </Avatar>
          <div className="grid flex-1 text-left text-sm leading-tight">
            <span className="truncate font-medium">{user.fullName}</span>
            <span className="truncate text-xs">{user.email}</span>
          </div>
        </div>
      </DropdownMenuLabel>
      <DropdownMenuSeparator />
      <DropdownMenuGroup>
        <DropdownMenuItem className="cursor-pointer" asChild>
          <Link href="/">
            <Scale className="mr-2 h-4 w-4" />
            Trang chủ
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem className="cursor-pointer" asChild>
          <Link href="/chat">
            <MessagesSquare className="mr-2 h-4 w-4" />
            Hỏi đáp pháp luật
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem className="cursor-pointer" asChild>
          <Link href="/conversations">
            <MessagesSquare className="mr-2 h-4 w-4" />
            Hội thoại của tôi
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem className="cursor-pointer" asChild>
          <Link href="/profile">
            <UserIcon className="mr-2 h-4 w-4" />
            Hồ sơ
          </Link>
        </DropdownMenuItem>
        {isAdmin && (
          <DropdownMenuItem className="cursor-pointer" asChild>
            <Link href="/admin/dashboard">
              <LayoutDashboard className="mr-2 h-4 w-4" />
              Quản trị
            </Link>
          </DropdownMenuItem>
        )}
      </DropdownMenuGroup>
      <DropdownMenuSeparator />
      <DropdownMenuItem
        onClick={handleLogout}
        variant="destructive"
        className="cursor-pointer"
      >
        <LogOut className="text-destructive mr-2 h-4 w-4" />
        Đăng xuất
      </DropdownMenuItem>
    </DropdownMenuContent>
  );
}

/**
 * Dropdown user cho **top header** (hoạt động cả mobile & desktop).
 * Guest: nút "Đăng nhập". User: avatar trigger + dropdown (`UserMenuContent`).
 */
export function UserMenu() {
  const user = useAuthStore((state) => state.user);

  if (!user) {
    return (
      <Button asChild size="sm" className="cursor-pointer">
        <Link href="/auth/login">
          <LogIn className="mr-1 h-4 w-4" />
          Đăng nhập
        </Link>
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Menu tài khoản"
          className="cursor-pointer rounded-full outline-none ring-ring transition-shadow focus-visible:ring-2"
        >
          <Avatar className="h-8 w-8 rounded-lg">
            <AvatarImage src={user.avatarUrl ?? undefined} alt={user.fullName ?? user.username} />
            <AvatarFallback className="rounded-lg">CN</AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>
      <UserMenuContent sideOffset={4} className="min-w-56 rounded-lg" />
    </DropdownMenu>
  );
}
