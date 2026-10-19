// Api response types
export interface ApiResponse<T = any> {
  success: boolean;
  statusCode: number;
  message: string;
  result: T;
}

export interface ApiPaginatedResponse<T = any> extends ApiResponse<T> {
  pagination: Pagination;
}

/** Khớp payload `pagination` của backend: `{ total, page, limit, totalPages }`. */
export interface Pagination {
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export type ApiErrorResponse = {
  success: false;
  statusCode: number;
  message: string;
  errors?: string[];
};

export type BaseDto = {
  createdAt: Date;
  createdBy: string;
  updatedAt: Date;
  updatedBy: string;
};

// login
export interface LoginData {
  username: string;
  password: string;
}

// register
export interface RegisterData {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

// role
export interface Role extends BaseDto {
  id: string;
  name: string;
  code: string;
  description?: string;
}

// User
export interface User extends BaseDto {
  id: string;
  email: string;
  fullName: string;
  status: string;
  isVerified: boolean;
  phoneNumber?: string;
  avatarUrl?: string;
  gender?: string;
  preferenceData?: Record<string, string[]>;
  birthDate?: Date;
  address?: string;
  roles: Role[];
}

// genres
export interface Genre {
  id: string;
  name: string;
  /** Tên tiếng Anh (backend `CreateGenreDto.enName`). */
  enName?: string;
}

export interface UpdateProfileDto {
  fullName?: string;
  avatarUrl?: string;
  phoneNumber?: string;
  birthDate?: Date;
  gender?: string;
  preferenceData?: Record<string, any>;
}

// update password
export interface UpdatePasswordData {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
}

// Old
// =============
export type ApiErrorBody = {
  success: false;
  message: string;
  details?: string[];
};

export type ApiOkBody<T> = {
  success: true;
  message: string;
  data: T;
};
// Old
// =============
