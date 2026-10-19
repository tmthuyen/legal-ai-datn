import { commentApi } from '@/apis/comment.api';
import { countryApi } from '@/apis/country.api';
import { genreApi } from '@/apis/genre.api';
import { interactionApi } from '@/apis/interaction.api';
import { movieApi, MovieAdminInput } from '@/apis/movie.api';
import { peopleApi, PeopleInput } from '@/apis/people.api';
import { ratingApi } from '@/apis/rating.api';
import { roleApi, RoleInput } from '@/apis/role.api';
import { userApi } from '@/apis/user.api';
import { Genre, Role, User } from '@/shared/types/api.types';
import { Country, Movie, People } from '@/shared/types/movie.types';
import { createCrudHooks, useDeleteOnly, usePagedList } from './admin-crud';

/**
 * Bộ hooks CRUD admin theo domain — mỗi domain dùng chung factory `createCrudHooks`
 * (query list phân trang + create/update/delete với invalidate + toast).
 * QueryKey root riêng `admin-*` để không conflict shape cache phía user.
 */

export const adminGenres = createCrudHooks<Genre, { name: string; enName?: string }>({
  domain: 'admin-genres',
  list: genreApi.getAll,
  create: genreApi.create,
  update: (id, data) => genreApi.update(id, data),
  remove: genreApi.delete,
});

export const adminCountries = createCrudHooks<Country, { name: string; code: string }>({
  domain: 'admin-countries',
  list: countryApi.getAll,
  create: countryApi.create,
  update: (id, data) => countryApi.update(id, data),
  remove: countryApi.remove,
});

export const adminPeoples = createCrudHooks<People, PeopleInput>({
  domain: 'admin-peoples',
  list: peopleApi.getAll,
  create: peopleApi.create,
  update: (id, data) => peopleApi.update(id, data),
  remove: peopleApi.remove,
});

export const adminMovies = createCrudHooks<Movie, MovieAdminInput>({
  domain: 'admin-movies',
  list: movieApi.getAll,
  create: movieApi.create,
  update: (id, data) => movieApi.update(id, data),
  remove: movieApi.remove,
});

/** Users — id là uuid (string); gán vai trò qua `PATCH /users/:id/roles` (form riêng). */
export type AdminUserInput = {
  /** Bắt buộc khi tạo; bỏ qua khi cập nhật (`UpdateProfileDto` không nhận email). */
  email?: string;
  fullName: string;
  password?: string;
  confirmPassword?: string;
};

export const adminUsers = createCrudHooks<User, AdminUserInput>({
  domain: 'admin-users',
  list: userApi.getAllUsers,
  create: userApi.createUser,
  update: (id, data) => userApi.updateUserAdmin(id, data),
  remove: userApi.deleteUser,
});

/**
 * Roles — backend `GET /api/roles` không phân trang → giả lập envelope
 * (`limit: 1000`, `totalPages: 1`) để dùng chung `DataTable`.
 */
const rolesListNoPagination = async () => {
  const response = await roleApi.getAll();
  return {
    ...response,
    pagination: { total: response.result?.length ?? 0, page: 1, limit: 1000, totalPages: 1 },
  };
};

export const adminRoles = createCrudHooks<Role, RoleInput>({
  domain: 'admin-roles',
  list: rolesListNoPagination,
  create: roleApi.create,
  update: (id, data) => roleApi.update(id, data),
  remove: roleApi.remove,
});

/**
 * Trang admin Interaction — 3 danh sách read-only (tương tác/đánh giá/bình luận)
 * + xóa từng bản ghi. Backend không filter theo type → filter client-side.
 */
/* eslint-disable react-hooks/rules-of-hooks -- usePagedList là FACTORY (trả về hook), không gọi hook nào khi chạy ở module level;see admin-crud.ts */
export const useAdminInteractions = usePagedList('admin-interactions', (params) =>
  interactionApi.getAll(params),
);
export const useAdminRatings = usePagedList('admin-ratings', (params) => ratingApi.getAll(params));
export const useAdminComments = usePagedList('admin-comments', (params) =>
  commentApi.getAll(params),
);
/* eslint-enable react-hooks/rules-of-hooks */

export const useDeleteInteraction = () => useDeleteOnly('admin-interactions', interactionApi.remove);
export const useDeleteRating = () => useDeleteOnly('admin-ratings', ratingApi.remove);
export const useDeleteComment = () => useDeleteOnly('admin-comments', commentApi.remove);
