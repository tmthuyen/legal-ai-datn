'use client';

import { Search, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';

/** Điều hướng tới trang danh sách phim với keyword trên URL (share được, seed được). */
function useSearchSubmit() {
  const router = useRouter();

  return (keyword: string) => {
    const trimmed = keyword.trim();
    router.push(trimmed ? `/movies?keyword=${encodeURIComponent(trimmed)}` : '/movies');
  };
}

/**
 * Ô tìm kiếm **kiểu YouTube** cho header — dùng chung logic submit:
 * - `md+`: input inline trong hàng header (biến `className` để header căn giữa còn lại).
 * - `< md`: chỉ hiện icon — mở rộng do `MobileSearchExpanded` đảm nhiệm.
 */
export function DesktopSearch() {
  const [value, setValue] = useState('');
  const submitSearch = useSearchSubmit();

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    submitSearch(value);
  };

  return (
    <form
      role="search"
      aria-label="Tìm phim"
      onSubmit={handleSubmit}
      className="relative hidden w-full max-w-md md:flex"
    >
      <Search
        className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
        aria-hidden="true"
      />
      <input
        type="search"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Tìm phim…"
        aria-label="Tìm phim theo tên"
        className="border-input bg-background/60 placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-full border py-1.5 pr-3 pl-9 text-sm outline-none transition-colors focus-visible:ring-2"
      />
      <button
        type="submit"
        aria-label="Tìm kiếm"
        className="bg-accent text-accent-foreground hover:bg-accent/70 absolute right-0 flex h-9 w-10 items-center justify-center rounded-full border transition-colors"
      >
        <Search className="size-4" aria-hidden="true" />
      </button>
    </form>
  );
}

/** Icon tìm kiếm trên mobile (`< md`) — bấm để mở hàng tìm kiếm mở rộng. */
export function MobileSearchToggle({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Mở tìm kiếm"
      className="text-muted-foreground hover:bg-accent flex size-9 items-center justify-center rounded-full transition-colors md:hidden"
    >
      <Search className="size-5" aria-hidden="true" />
    </button>
  );
}

/**
 * Hàng tìm kiếm **mở rộng trên mobile** (thay nguyên hàng header, kiểu YouTube):
 * nút đóng bên trái + input autoFocus + nút submit.
 */
export function MobileSearchExpanded({ onClose }: { onClose: () => void }) {
  const [value, setValue] = useState('');
  const submitSearch = useSearchSubmit();

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    submitSearch(value);
    onClose();
  };

  return (
    <form
      role="search"
      aria-label="Tìm phim"
      onSubmit={handleSubmit}
      className="flex w-full items-center gap-2 md:hidden"
    >
      <button
        type="button"
        onClick={onClose}
        aria-label="Đóng tìm kiếm"
        className="text-muted-foreground hover:bg-accent flex size-9 shrink-0 items-center justify-center rounded-full transition-colors"
      >
        <X className="size-5" aria-hidden="true" />
      </button>
      <input
        type="search"
        autoFocus
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Tìm phim…"
        aria-label="Tìm phim theo tên"
        className="border-input bg-background/60 placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full min-w-0 rounded-full border px-3 text-sm outline-none transition-colors focus-visible:ring-2"
      />
      <button
        type="submit"
        aria-label="Tìm kiếm"
        className="bg-accent text-accent-foreground hover:bg-accent/70 flex size-9 shrink-0 items-center justify-center rounded-full border transition-colors"
      >
        <Search className="size-4" aria-hidden="true" />
      </button>
    </form>
  );
}
