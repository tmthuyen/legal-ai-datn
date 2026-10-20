import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { hierarchyKeyLabel, HierarchyEntry } from '@/shared/utils/legal';

interface LegalHierarchyBreadcrumbProps {
  /** Danh sách entry phân cấp đã chuẩn hoá từ `extractedHierarchy`. */
  entries: HierarchyEntry[];
  className?: string;
}

/**
 * Breadcrumb hiển thị phân cấp luật mà AI trích xuất từ câu hỏi
 * (vd. `Văn bản › Chương › Điều › Khoản`). Dùng `Breadcrumb` shadcn/ui có sẵn.
 */
export function LegalHierarchyBreadcrumb({ entries, className }: LegalHierarchyBreadcrumbProps) {
  if (entries.length === 0) return null;

  return (
    <Breadcrumb className={className}>
      <BreadcrumbList>
        {entries.map((entry, index) => (
          <span key={`${entry.label}-${index}`} className="contents">
            <BreadcrumbItem>
              <BreadcrumbPage className="inline-flex items-center gap-1">
                <span className="text-muted-foreground">{hierarchyKeyLabel(entry.label)}:</span>
                <span>{entry.value}</span>
              </BreadcrumbPage>
            </BreadcrumbItem>
            {index < entries.length - 1 ? <BreadcrumbSeparator /> : null}
          </span>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
