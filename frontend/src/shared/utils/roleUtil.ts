import { LegalUser, UserRole } from '@/shared/types/legal.types';

/**
 * Tiện ích vai trò cho Legal AI.
 *
 * Contract chỉ định nghĩa **một** field `role` trên `User` với 2 giá trị `user` | `admin`,
 * nên các helper ở đây làm việc trực tiếp trên `role` (không dùng mảng `roles` kiểu cũ).
 */

/** Chuẩn hoá role về mã chữ hoa để so khớp với guard (`'ADMIN'`). */
const roleToCode = (role: UserRole | null | undefined): string =>
  (role ?? '').toUpperCase();

/** Kiểm tra user có vai trò admin hay không. */
const isAdmin = (user: LegalUser | null | undefined): boolean => roleToCode(user?.role) === 'ADMIN';

/** Lấy mã vai trò (chữ hoa) của user; trả mảng rỗng nếu chưa đăng nhập. */
const mapRoleToCodes = (user: LegalUser | null | undefined): string[] => {
  if (!user) return [];
  return [roleToCode(user.role)].filter(Boolean);
};

/** Trang mặc định sau đăng nhập theo vai trò (admin → `/admin/dashboard`, còn lại → trang chủ). */
const getHomeRouteByRole = (user: LegalUser | null | undefined): string => {
  if (isAdmin(user)) return '/admin/dashboard';
  return '/';
};

export const roleUtil = {
  roleToCode,
  isAdmin,
  mapRoleToCodes,
  getHomeRouteByRole,
};
