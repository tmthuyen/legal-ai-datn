/**
 * Narrow dữ liệu `relatedNodes` / `extractedHierarchy` trả về từ Backend (qua Services).
 *
 * Contract khai báo `relatedNodes: unknown[] | null` và
 * `extractedHierarchy: Record<string, unknown> | null` (không ràng buộc schema chặt),
 * nên UI chỉ đọc các field **tuỳ chọn** và bỏ qua nếu thiếu — không giả định cứng,
 * không dùng `any`.
 */

/** Một node luật liên quan (Điều/Khoản/Điểm/Văn bản…) đã được narrow an toàn. */
export interface RelatedNode {
  nodeId: string | null;
  type: string | null;
  title: string | null;
  /** Số hiển thị của node (Điều/Chương…); có thể là number hoặc string. */
  number: string | null;
  text: string | null;
  citation: string | null;
  /** Các key khác giữ nguyên để hiển thị phụ trợ nếu cần. */
  raw: Record<string, unknown>;
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

/** Đọc một field bất kỳ dưới dạng chuỗi (chấp nhận string/number), trả null nếu không có. */
const asString = (value: unknown): string | null => {
  if (typeof value === 'string') return value;
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  return null;
};

/** Narrow 1 phần tử `unknown` thành `RelatedNode` (các field thiếu → null). */
export const toRelatedNode = (value: unknown): RelatedNode | null => {
  if (!isRecord(value)) return null;
  return {
    nodeId: asString(value.node_id ?? value.nodeId),
    type: asString(value.type),
    title: asString(value.title),
    number: asString(value.number),
    text: asString(value.text ?? value.full_text ?? value.fullText),
    citation: asString(value.citation),
    raw: value,
  };
};

/** Narrow mảng `relatedNodes` (bỏ phần tử không hợp lệ). */
export const toRelatedNodes = (value: unknown): RelatedNode[] => {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => toRelatedNode(item))
    .filter((node): node is RelatedNode => node !== null);
};

/** Một mục phân cấp luật (nhãn + giá trị) để render breadcrumb. */
export interface HierarchyEntry {
  label: string;
  value: string;
}

/**
 * Chuẩn hoá `extractedHierarchy` (object tự do) thành danh sách entry để render.
 * Ví dụ `{ document: "Hiến pháp 2013", article: "Điều 1" }` → 2 entry.
 */
export const toHierarchyEntries = (value: unknown): HierarchyEntry[] => {
  if (!isRecord(value)) return [];
  return Object.entries(value)
    .map(([key, raw]) => ({ key, value: toHierarchyValue(raw) }))
    .filter((entry): entry is { key: string; value: string } => entry.value !== null)
    .map((entry) => ({ label: entry.key, value: entry.value }));
};

/** Chuyển giá trị phân cấp (string/number/array/object) thành chuỗi hiển thị ngắn gọn. */
const toHierarchyValue = (raw: unknown): string | null => {
  if (typeof raw === 'string') return raw;
  if (typeof raw === 'number') return String(raw);
  if (Array.isArray(raw)) {
    const parts = raw.map((item) => toHierarchyValue(item)).filter((v): v is string => !!v);
    return parts.length ? parts.join(' › ') : null;
  }
  if (isRecord(raw)) {
    const label = raw.title ?? raw.name ?? raw.label ?? raw.citation;
    return asString(label);
  }
  return null;
};

/** Nhãn tiếng Việt cho `type` của node luật (Backend trả theo label đồ thị). */
export const NODE_TYPE_LABELS: Record<string, string> = {
  Document: 'Văn bản',
  Part: 'Phần',
  Chapter: 'Chương',
  Section: 'Mục',
  SubSection: 'Tiểu mục',
  Article: 'Điều',
  Clause: 'Khoản',
  Point: 'Điểm',
};

/** Nhãn hiển thị cho `type` (fallback về chính `type`). */
export const nodeTypeLabel = (type: string | null): string =>
  type ? (NODE_TYPE_LABELS[type] ?? type) : 'Trích dẫn';

/** Nhãn tiếng Việt cho key của `extractedHierarchy` (fallback về key gốc). */
export const HIERARCHY_KEY_LABELS: Record<string, string> = {
  document: 'Văn bản',
  document_id: 'Mã văn bản',
  documentId: 'Mã văn bản',
  part: 'Phần',
  chapter: 'Chương',
  section: 'Mục',
  subsection: 'Tiểu mục',
  subSection: 'Tiểu mục',
  article: 'Điều',
  clause: 'Khoản',
  point: 'Điểm',
  number: 'Số',
  title: 'Tiêu đề',
};

/** Nhãn hiển thị cho key phân cấp. */
export const hierarchyKeyLabel = (key: string): string => HIERARCHY_KEY_LABELS[key] ?? key;
