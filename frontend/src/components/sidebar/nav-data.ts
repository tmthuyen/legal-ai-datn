import {
  BarChart4,
  ContactRound,
  LayoutDashboard,
  LogIn,
  MessagesSquare,
  Scale,
  Settings,
  User as UserIcon,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  title: string;
  url: string;
  icon: LucideIcon;
}

export interface NavSectionData {
  groupLabel: string;
  items: NavItem[];
}

/**
 * **Nguồn dữ liệu điều hướng duy nhất** — dùng chung cho sidebar (`nav-main`),
 * dropdown "Điều hướng nhanh" trên header (`quick-nav-dropdown`) và bottom nav
 * mobile (`mobile-bottom-nav`). Chỉ chứa route pháp luật của Legal AI.
 */
export const NAV_SECTIONS = {
  user: {
    groupLabel: 'Pháp luật',
    items: [
      {
        title: 'Trang chủ',
        url: '/',
        icon: Scale,
      },
      {
        title: 'Hỏi đáp pháp luật',
        url: '/chat',
        icon: MessagesSquare,
      },
      {
        title: 'Hội thoại của tôi',
        url: '/conversations',
        icon: MessagesSquare,
      },
    ],
  },
  admin: {
    groupLabel: 'Quản trị',
    items: [
      {
        title: 'Tổng quan',
        url: '/admin/dashboard',
        icon: LayoutDashboard,
      },
      {
        title: 'Người dùng',
        url: '/admin/users',
        icon: ContactRound,
      },
    ],
  },
  settings: {
    groupLabel: 'Cá nhân',
    items: [
      {
        title: 'Hồ sơ',
        url: '/profile',
        icon: UserIcon,
      },
      {
        title: 'Cài đặt',
        url: '/setting/theme',
        icon: Settings,
      },
    ],
  },
  auth: {
    groupLabel: 'Tài khoản',
    items: [
      {
        title: 'Đăng nhập',
        url: '/auth/login',
        icon: LogIn,
      },
    ],
  },
} satisfies Record<string, NavSectionData>;

export type NavSectionKey = keyof typeof NAV_SECTIONS;

export interface BottomNavItemData {
  href: string;
  label: string;
  icon: LucideIcon;
  /** So khớp chặt (`===`) thay vì `startsWith` — dùng cho trang gốc. */
  exact?: boolean;
  /** Chỉ hiển thị khi đã đăng nhập. */
  requiresAuth?: boolean;
  /** Chỉ hiển thị khi chưa đăng nhập (guest). */
  guestOnly?: boolean;
}

/**
 * Item bottom nav mobile (`< md`) cho **cả user & admin** — tách khỏi sidebar vì
 * mobile không hiển thị sidebar; nhãn rút gọn để vừa 1 hàng.
 */
export const BOTTOM_NAV: Record<'user' | 'admin', BottomNavItemData[]> = {
  user: [
    { href: '/', label: 'Trang chủ', icon: Scale, exact: true },
    { href: '/chat', label: 'Hỏi đáp', icon: MessagesSquare },
    { href: '/conversations', label: 'Hội thoại', icon: MessagesSquare, requiresAuth: true },
    { href: '/profile', label: 'Tài khoản', icon: UserIcon, requiresAuth: true },
    { href: '/auth/login', label: 'Đăng nhập', icon: LogIn, guestOnly: true },
  ],
  admin: [
    { href: '/admin/dashboard', label: 'Tổng quan', icon: LayoutDashboard, exact: true },
    { href: '/admin/users', label: 'Người dùng', icon: ContactRound },
    { href: '/chat', label: 'Hỏi đáp', icon: MessagesSquare },
    { href: '/profile', label: 'Hồ sơ', icon: UserIcon },
  ],
};

/** Nhãn thống kê dùng chung cho dashboard admin (tránh lặp hằng số). */

/** Icon đại diện nhóm thống kê admin. */
export const ADMIN_ANALYTICS_ICON: LucideIcon = BarChart4;
