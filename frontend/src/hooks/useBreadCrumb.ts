'use client';

import { usePathname } from 'next/navigation';

export function useBreadcrumbs() {
  const pathname = usePathname();

  return pathname
    .split('/')
    .filter(Boolean)
    .map((segment, index, arr) => ({
      label: segment,
      href: '/' + arr.slice(0, index + 1).join('/'),
    }));
}
