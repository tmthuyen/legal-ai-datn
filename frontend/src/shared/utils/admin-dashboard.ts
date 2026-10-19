import { Comment } from '@/shared/types/comment.types';
import { Interaction, InteractionType } from '@/shared/types/interaction.types';
import { Movie } from '@/shared/types/movie.types';
import { Rating } from '@/shared/types/rating.types';
import { formatDateTime } from '@/shared/utils/formatting';
import { getMovieTitle } from '@/shared/utils/movie';

/**
 * Tính toán thống kê cho **dashboard admin** — hàm thuần (không React), tách khỏi UI
 * để dùng lại/kiểm thử được. Lưu ý: backend chưa có endpoint aggregate, mọi số liệu
 * ở đây tính trên **mẫu N bản ghi đầu** của list API (trừ `pagination.total`).
 */

export interface ChartDatum {
  label: string;
  value: number;
}

/** Nhãn cho nhóm dữ liệu gộp lại (biểu đồ quá dài). */
export const OTHER_LABEL = 'Khác';

/** Nhãn cho dữ liệu thiếu trường phân loại. */
export const UNKNOWN_LABEL = 'Chưa xác định';

export type ActivityKind = 'interaction' | 'rating' | 'comment';

/** Một dòng cho bảng "Hoạt động gần đây". */
export interface RecentActivityItem {
  id: string;
  kind: ActivityKind;
  createdAt?: string | Date;
  /** Tên người dùng (join `user`) — fallback email. */
  userName: string;
  userEmail?: string;
  /** Tiêu đề phim (join `movie`). */
  movieTitle: string;
  /** Mô tả ngắn theo loại (loại tương tác / số sao / trích bình luận). */
  detail: string;
  /** Nhãn loại để render badge. */
  kindLabel: string;
}

/** Đếm số lần xuất hiện theo khóa (bỏ qua khóa rỗng). */
function countValues<T>(items: T[], getKey: (item: T) => string | undefined | null) {
  const counts = new Map<string, number>();
  items.forEach((item) => {
    const key = getKey(item);
    if (!key) return;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  });
  return counts;
}

/** Sắp xếp giảm dần, lấy top `limit`, phần còn lại gộp thành "Khác". */
export function toTopWithOther(counts: Map<string, number>, limit: number): ChartDatum[] {
  const sorted = [...counts.entries()].sort((left, right) => right[1] - left[1]);
  const top = sorted.slice(0, limit).map(([label, value]) => ({ label, value }));
  const rest = sorted.slice(limit).reduce((sum, [, value]) => sum + value, 0);
  if (rest > 0) top.push({ label: OTHER_LABEL, value: rest });
  return top;
}

/** Top phim theo lượt xem (`viewCount` — backend không sort nên sắp xếp client-side). */
export function buildTopMoviesByViews(movies: Movie[], limit = 10) {
  return [...movies]
    .sort((left, right) => Number(right.viewCount ?? 0) - Number(left.viewCount ?? 0))
    .slice(0, limit)
    .map((movie) => ({ label: getMovieTitle(movie), value: Number(movie.viewCount ?? 0) }));
}

/** Phân bố phim theo thể loại (một phim có nhiều thể loại → đếm theo từng thể loại). */
export function buildGenreDistribution(movies: Movie[], limit = 10) {
  const counts = new Map<string, number>();
  movies.forEach((movie) =>
    movie.genres?.forEach((genre) => counts.set(genre.name, (counts.get(genre.name) ?? 0) + 1)),
  );
  return toTopWithOther(counts, limit);
}

/** Phân bố phim theo quốc gia. */
export function buildCountryDistribution(movies: Movie[], limit = 10) {
  const counts = countValues(movies, (movie) => movie.country?.name ?? UNKNOWN_LABEL);
  return toTopWithOther(counts, limit);
}

/** Phân bố tương tác theo loại (giữ `type` để component tự map nhãn). */
export function buildInteractionTypeDistribution(interactions: Interaction[]) {
  const counts = countValues(interactions, (item) => item.type);
  return [...counts.entries()]
    .sort((left, right) => right[1] - left[1])
    .map(([type, value]) => ({ type: type as InteractionType, value }));
}

/** Phân bố đánh giá theo số sao — luôn có đủ cột 1..5 (kể cả giá trị 0) để so sánh được. */
export function buildRatingDistribution(ratings: Rating[]) {
  const buckets = [1, 2, 3, 4, 5].map((star) => ({
    label: `${star} sao`,
    value: ratings.filter((rating) => Math.round(Number(rating.rating)) === star).length,
  }));
  const zero = ratings.filter((rating) => Math.round(Number(rating.rating)) <= 0).length;
  if (zero > 0) buckets.unshift({ label: '0 sao', value: zero });
  return buckets;
}

/**
 * Top phim điểm cao nhất theo **điểm trung bình** (chỉ tính phim đủ `minVotes` lượt
 * trong mẫu để tránh 1 đánh giá 5★ đứng đầu).
 */
export function buildTopRatedMovies(ratings: Rating[], limit = 10, minVotes = 2) {
  const stats = new Map<string, { title: string; total: number; votes: number }>();
  ratings.forEach((rating) => {
    const title = rating.movie ? getMovieTitle(rating.movie) : undefined;
    if (!title) return;
    const current = stats.get(title) ?? { title, total: 0, votes: 0 };
    current.total += Number(rating.rating ?? 0);
    current.votes += 1;
    stats.set(title, current);
  });
  return [...stats.values()]
    .filter((entry) => entry.votes >= minVotes)
    .map((entry) => ({
      label: entry.title,
      value: Math.round((entry.total / entry.votes) * 10) / 10,
      votes: entry.votes,
    }))
    .sort((left, right) => right.value - left.value)
    .slice(0, limit);
}

/** Top người dùng hoạt động nhiều nhất (gộp tương tác + đánh giá + bình luận trong mẫu). */
export function buildTopActiveUsers(
  records: Array<{ user?: { id?: string; fullName?: string; email?: string } }>,
  limit = 10,
) {
  const counts = countValues(records, (record) =>
    record.user?.fullName || record.user?.email || undefined,
  );
  return toTopWithOther(counts, limit);
}

/** Cảnh báo dữ liệu phim thiếu trường (tính trên mẫu) + link sang trang quản trị. */
export interface DataQualityIssue {
  label: string;
  description: string;
  count: number;
  href: string;
}

export function buildDataQualityIssues(movies: Movie[]): DataQualityIssue[] {
  const missing = (predicate: (movie: Movie) => boolean) => movies.filter(predicate).length;
  return [
    {
      label: 'Thiếu poster',
      description: 'Phim không có ảnh poster — hiển thị xấu ở danh sách/chi tiết.',
      count: missing((movie) => !movie.posterPath),
      href: '/admin/movies',
    },
    {
      label: 'Thiếu mô tả',
      description: 'Chưa có `overview`/`overviewVi`.',
      count: missing((movie) => !movie.overview && !movie.overviewVi),
      href: '/admin/movies',
    },
    {
      label: 'Chưa gắn thể loại',
      description: 'Không có thể loại → không xuất hiện trong lọc theo thể loại.',
      count: missing((movie) => !movie.genres || movie.genres.length === 0),
      href: '/admin/movies',
    },
    {
      label: 'Chưa gắn quốc gia',
      description: 'Không có quốc gia sản xuất.',
      count: missing((movie) => !movie.country),
      href: '/admin/movies',
    },
  ];
}

/**
 * Lọc bản ghi trong `days` ngày gần nhất (`days = 0` → lấy tất cả).
 * ⚠ Chỉ áp dụng trên mẫu đã tải — backend chưa hỗ trợ filter theo thời gian.
 */
export function filterWithinDays<T extends { createdAt?: string | Date }>(
  items: T[],
  days: number,
): T[] {
  if (!days) return items;
  const threshold = Date.now() - days * 24 * 60 * 60 * 1000;
  return items.filter((item) => {
    if (!item.createdAt) return false;
    return new Date(item.createdAt).getTime() >= threshold;
  });
}

const KIND_LABELS: Record<ActivityKind, string> = {
  interaction: 'Tương tác',
  rating: 'Đánh giá',
  comment: 'Bình luận',
};

/** Gộp tương tác + đánh giá + bình luận thành 1 dòng thời gian hoạt động (mới nhất trước). */
export function buildRecentActivity({
  interactions,
  ratings,
  comments,
  limit = 10,
}: {
  interactions: Interaction[];
  ratings: Rating[];
  comments: Comment[];
  limit?: number;
}): RecentActivityItem[] {
  const items: RecentActivityItem[] = [
    ...interactions.map((item) => ({
      id: `interaction-${item.id}`,
      kind: 'interaction' as const,
      createdAt: item.createdAt,
      userName: item.user?.fullName || item.user?.email || '—',
      userEmail: item.user?.email,
      movieTitle: item.movie ? getMovieTitle(item.movie) : '—',
      detail: item.type,
      kindLabel: KIND_LABELS.interaction,
    })),
    ...ratings.map((item) => ({
      id: `rating-${item.id}`,
      kind: 'rating' as const,
      createdAt: item.createdAt,
      userName: item.user?.fullName || item.user?.email || '—',
      userEmail: item.user?.email,
      movieTitle: item.movie ? getMovieTitle(item.movie) : '—',
      detail: `${Number(item.rating ?? 0)} sao`,
      kindLabel: KIND_LABELS.rating,
    })),
    ...comments.map((item) => ({
      id: `comment-${item.id}`,
      kind: 'comment' as const,
      createdAt: item.createdAt,
      userName: item.user?.fullName || item.user?.email || '—',
      userEmail: item.user?.email,
      movieTitle: item.movie ? getMovieTitle(item.movie) : '—',
      detail: item.content,
      kindLabel: KIND_LABELS.comment,
    })),
  ];

  return items
    .sort(
      (left, right) =>
        new Date(right.createdAt ?? 0).getTime() - new Date(left.createdAt ?? 0).getTime(),
    )
    .slice(0, limit);
}

/** Chuỗi thời gian hiển thị cho bảng hoạt động. */
export function formatActivityTime(value?: string | Date) {
  return value ? formatDateTime(value) : '—';
}

/** Escape 1 ô CSV (bọc `"`, nhân đôi `"` bên trong). */
function escapeCsvCell(value: string | number) {
  const text = String(value ?? '');
  return `"${text.replace(/"/g, '""')}"`;
}

/** Chuyển mảng object phẳng thành CSV (có header). */
export function toCsv(rows: Array<Record<string, string | number>>): string {
  if (rows.length === 0) return '';
  const headers = Object.keys(rows[0]);
  const lines = [
    headers.map(escapeCsvCell).join(','),
    ...rows.map((row) => headers.map((header) => escapeCsvCell(row[header] ?? '')).join(',')),
  ];
  return lines.join('\r\n');
}

/**
 * Tải file CSV phía client (chỉ gọi trong handler click — không chạy khi SSR).
 * Thêm BOM để Excel đọc đúng tiếng Việt (UTF-8).
 */
export function downloadCsv(filename: string, csv: string) {
  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
