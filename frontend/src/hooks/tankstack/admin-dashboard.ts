import {
  adminGenres,
  adminMovies,
  adminUsers,
  useAdminComments,
  useAdminInteractions,
  useAdminRatings,
} from '@/hooks/tankstack/admin';
import {
  buildCountryDistribution,
  buildDataQualityIssues,
  buildGenreDistribution,
  buildInteractionTypeDistribution,
  buildRatingDistribution,
  buildRecentActivity,
  buildTopActiveUsers,
  buildTopMoviesByViews,
  buildTopRatedMovies,
  filterWithinDays,
} from '@/shared/utils/admin-dashboard';
import { useQueryClient } from '@tanstack/react-query';
import { useMemo } from 'react';

/** Số bản ghi tối đa lấy về để tính thống kê client-side (backend chưa có endpoint aggregate). */
export const DASHBOARD_SAMPLE_LIMIT = 100;

/** Số mục hiển thị trên mỗi biểu đồ / bảng xếp hạng. */
export const DASHBOARD_TOP_COUNT = 10;

/** QueryKey root của các list dùng cho dashboard — dùng để làm mới toàn bộ. */
const DASHBOARD_QUERY_ROOTS = [
  'admin-movies',
  'admin-genres',
  'admin-users',
  'admin-interactions',
  'admin-ratings',
  'admin-comments',
];

/**
 * Gom **mọi** query + phép tính của dashboard admin vào 1 hook: mỗi list API chỉ gọi
 * 1 lần (lấy `pagination.total` cho thẻ chỉ số và `limit` bản ghi cho biểu đồ),
 * phần tổng hợp tách sang `shared/utils/admin-dashboard.ts`.
 *
 * `days = 0` → không lọc thời gian (backend chưa hỗ trợ filter theo ngày, nên bộ lọc
 * chỉ áp dụng trên bảng "Hoạt động gần đây" của mẫu đã tải).
 */
export function useAdminDashboard({
  sampleLimit = DASHBOARD_SAMPLE_LIMIT,
  days = 0,
}: { sampleLimit?: number; days?: number } = {}) {
  const queryClient = useQueryClient();

  const moviesQuery = adminMovies.useList({ page: 1, limit: sampleLimit });
  const genresQuery = adminGenres.useList({ page: 1, limit: 1 });
  const usersQuery = adminUsers.useList({ page: 1, limit: 1 });
  const interactionsQuery = useAdminInteractions({ page: 1, limit: sampleLimit });
  const ratingsQuery = useAdminRatings({ page: 1, limit: sampleLimit });
  const commentsQuery = useAdminComments({ page: 1, limit: sampleLimit });

  // Giữ tham chiếu gốc trong deps (không dùng `?? []` trực tiếp — tránh mảng mới mỗi render).
  const movieItems = moviesQuery.data?.items;
  const interactionItems = interactionsQuery.data?.items;
  const ratingItems = ratingsQuery.data?.items;
  const commentItems = commentsQuery.data?.items;

  const derived = useMemo(() => {
    const movies = movieItems ?? [];
    const interactions = interactionItems ?? [];
    const ratings = ratingItems ?? [];
    const comments = commentItems ?? [];
    return {
      topViewed: buildTopMoviesByViews(movies, DASHBOARD_TOP_COUNT),
      genreDistribution: buildGenreDistribution(movies, DASHBOARD_TOP_COUNT),
      countryDistribution: buildCountryDistribution(movies, DASHBOARD_TOP_COUNT),
      interactionTypes: buildInteractionTypeDistribution(interactions),
      ratingDistribution: buildRatingDistribution(ratings),
      topRated: buildTopRatedMovies(ratings, DASHBOARD_TOP_COUNT),
      topActiveUsers: buildTopActiveUsers(
        [...interactions, ...ratings, ...comments],
        DASHBOARD_TOP_COUNT,
      ),
      dataQualityIssues: buildDataQualityIssues(movies).filter((issue) => issue.count > 0),
      recentActivity: buildRecentActivity({
        interactions: filterWithinDays(interactions, days),
        ratings: filterWithinDays(ratings, days),
        comments: filterWithinDays(comments, days),
        limit: 12,
      }),
      /** Số bản ghi thực tế đang phân tích (mẫu) — hiển thị để không gây hiểu nhầm. */
      sampleSize: movies.length + interactions.length + ratings.length + comments.length,
    };
  }, [movieItems, interactionItems, ratingItems, commentItems, days]);

  const totals = {
    movies: moviesQuery.data?.pagination.total ?? 0,
    users: usersQuery.data?.pagination.total ?? 0,
    genres: genresQuery.data?.pagination.total ?? 0,
    interactions: interactionsQuery.data?.pagination.total ?? 0,
    ratings: ratingsQuery.data?.pagination.total ?? 0,
    comments: commentsQuery.data?.pagination.total ?? 0,
  };

  const queries = [
    moviesQuery,
    genresQuery,
    usersQuery,
    interactionsQuery,
    ratingsQuery,
    commentsQuery,
  ];

  return {
    totals,
    sampleLimit,
    ...derived,
    /** Chỉ true khi **mọi** list đang tải lần đầu (tránh nhấp nháy từng thẻ). */
    isLoading: queries.every((query) => query.isLoading),
    /** true khi list phim lỗi (dữ liệu biểu đồ chính) hoặc mọi list lỗi. */
    isError: moviesQuery.isError || queries.every((query) => query.isError),
    /** true khi còn bất kỳ list nào đang tải lại (dùng để disable nút "Làm mới"). */
    isFetching: queries.some((query) => query.isFetching),
    /** Tải lại toàn bộ dữ liệu dashboard từ server. */
    refresh: () => {
      DASHBOARD_QUERY_ROOTS.forEach((root) =>
        queryClient.invalidateQueries({ queryKey: [root] }),
      );
    },
  };
}
