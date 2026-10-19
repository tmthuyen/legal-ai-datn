'use client';

import { useAuthStore } from '@/stores/auth.store';
import { useEffect } from 'react';

export function AuthInit() {
  useEffect(() => {
    useAuthStore.getState().bootstrap();
  }, []);
  return null;
}
