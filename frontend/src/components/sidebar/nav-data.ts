import {
  Activity,
  BarChart4,
  Bell,
  Clock,
  ContactRound,
  Film,
  Flag,
  Heart,
  Home,
  LayoutDashboard,
  LogIn,
  Palette,
  Tag,
  User as UserIcon,
  UsersRound,
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
 * mobile (`mobile-bottom-nav`). Thêm/sửa route chỉ cần sửa ở đây.
 */
export const NAV_SECTIONS = {
  user: {
    groupLabel: 'Khám phá',
    items: [
      {
        title: 'Trang chủ',
        url: '/',
        icon: Home,
      },
      {
        title: 'Phim',
        url: '/movies',
        icon: Film,
      },
    ],
  },
  learning: {
    groupLabel: 'Dashboard',
    items: [
      {
        title: 'Dashboard',
        url: '/dashboard',
        icon: Home,
      },
    ],
  },
  auth: {
    groupLabel: 'Auth',
    items: [
      {
        title: 'Tài khoản',
        url: '/admin/users',
        icon: ContactRound,
      },
      {
        title: 'Vai trò',
        url: '/admin/roles',
        icon: BarChart4,
      },
    ],
  },
  admin: {
    groupLabel: 'Movie',
    items: [
      {
        title: 'Phim',
        url: '/admin/movies',
        icon: Film,
      },
      {
        title: 'Thể loại',
        url: '/admin/genres',
        icon: Tag,
      },
      {
        title: 'Quốc gia',
        url: '/admin/countries',
        icon: Flag,
      },
      {
        title: 'Diễn viên & đạo diễn',
        url: '/admin/people',
        icon: UsersRound,
      },
    ],
  },
  interaction: {
    groupLabel: 'Interaction',
    items: [
      {
        title: 'Tương tác',
        url: '/admin/interaction',
        icon: Activity,
      },
    ],
  },
  personal: {
    groupLabel: 'Cá nhân',
    items: [
      {
        title: 'Lịch sử xem',
        url: '/my-history',
        icon: Clock,
      },
      {
        title: 'Yêu thích',
        url: '/my-favorites',
        icon: Heart,
      },
    ],
  },
  settings: {
    groupLabel: 'Settings',
    items: [
      {
        title: 'Theme',
        url: '/setting/theme',
        icon: Palette,
      },
      {
        title: 'Hồ sơ',
        url: '/profile',
        icon: ContactRound,
      },
      {
        title: 'Thông báo',
        url: '/notification',
        icon: Bell,
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
 * mobile không hiển thị sidebar; nhãn rút gọn để vừa 1 hàng 5 item.
 */
export const BOTTOM_NAV: Record<'user' | 'admin', BottomNavItemData[]> = {
  user: [
    { href: '/', label: 'Trang chủ', icon: Home, exact: true },
    { href: '/movies', label: 'Phim', icon: Film },
    { href: '/notification', label: 'Thông báo', icon: Bell, requiresAuth: true },
    { href: '/profile', label: 'Tài khoản', icon: UserIcon, requiresAuth: true },
    { href: '/auth/login', label: 'Đăng nhập', icon: LogIn, guestOnly: true },
  ],
  admin: [
    { href: '/dashboard', label: 'Tổng quan', icon: LayoutDashboard, exact: true },
    { href: '/admin/movies', label: 'Phim', icon: Film },
    { href: '/admin/interaction', label: 'Tương tác', icon: Activity },
    { href: '/admin/users', label: 'Tài khoản', icon: ContactRound },
    { href: '/profile', label: 'Hồ sơ', icon: UserIcon },
  ],
};
