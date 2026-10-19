'use client';

import { Plus, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface CrudToolbarProps {
  keyword: string;
  onKeywordChange: (value: string) => void;
  searchPlaceholder?: string;
  onAdd: () => void;
  addLabel?: string;
  /** Ẩn nút thêm (danh sách read-only). */
  hideAdd?: boolean;
  className?: string;
}

/**
 * Toolbar dùng chung cho mọi trang CRUD admin: ô tìm kiếm (debounce do
 * `useCrudPage` xử lý) + nút "Thêm mới". Không lặp ở từng domain.
 */
export function CrudToolbar({
  keyword,
  onKeywordChange,
  searchPlaceholder = 'Tìm kiếm…',
  onAdd,
  addLabel = 'Thêm mới',
  hideAdd = false,
  className,
}: CrudToolbarProps) {
  return (
    <div className={`flex flex-wrap items-center gap-3 ${className ?? ''}`}>
      <div className="relative w-full max-w-sm flex-1">
        <Search
          className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
          aria-hidden="true"
        />
        <Input
          value={keyword}
          onChange={(event) => onKeywordChange(event.target.value)}
          placeholder={searchPlaceholder}
          aria-label={searchPlaceholder}
          className="pl-9"
        />
      </div>
      {!hideAdd ? (
        <Button onClick={onAdd} className="cursor-pointer">
          <Plus className="size-4" aria-hidden="true" />
          {addLabel}
        </Button>
      ) : null}
    </div>
  );
}
