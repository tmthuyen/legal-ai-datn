import { Metadata } from 'next';
import { Suspense } from 'react';
import VerifyEmail from '@/app/auth/verify-email/verify-email';

export const metadata: Metadata = {
  title: 'Xác thực email',
  description: 'Xác thực email | Movie Recommendation App',
};

function VerifyEmailContent() {
  console.log('VerifyEmail component rendered');
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      {/* VerifyEmail dùng useSearchParams → bắt buộc bọc Suspense khi prerender tĩnh */}
      <Suspense fallback={null}>
        <VerifyEmail />
      </Suspense>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center px-4">Loading...</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
