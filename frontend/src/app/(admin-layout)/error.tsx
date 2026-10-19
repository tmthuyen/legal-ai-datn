'use strict';
'use client'; // Bắt buộc phải là Client Component

import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCcw } from 'lucide-react';
import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log lỗi ra các dịch vụ như Sentry, LogRocket, v.v.
    console.error('Đã xảy ra lỗi:', error);
  }, [error]);

  return (
    <div className="flex w-full flex-col items-center justify-center rounded-2xl border border-2 border-red-200 bg-gray-50 p-8 dark:border-red-900/50 dark:bg-slate-900">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
        <AlertTriangle className="h-8 w-8 text-red-500" />
      </div>
      <h2 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">Đã có lỗi xảy ra!</h2>
      <p className="mb-6 max-w-md text-center text-gray-500 dark:text-gray-400">
        Rất xin lỗi, thành phần giao diện này đang gặp sự cố. Bạn vui lòng thử tải lại trang.
      </p>

      {import.meta.env.MODE === 'development' && error && (
        <div className="mb-6 w-full max-w-2xl overflow-auto rounded-lg bg-gray-900 p-4">
          <pre className="text-left font-mono text-xs text-red-400">{error.toString()}</pre>
        </div>
      )}

      <Button
        onClick={reset}
        className="rounded-xl bg-red-500 text-white shadow-lg shadow-red-500/20 hover:bg-red-600"
      >
        <RefreshCcw className="mr-2 h-4 w-4" />
        Tải lại trang
      </Button>
    </div>
  );
}
