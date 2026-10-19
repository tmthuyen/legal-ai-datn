import { Metadata } from 'next';
import { Suspense } from 'react';
import LoginForm from './login-form';

export const metadata: Metadata = {
  title: 'Login',
  description: 'Sign in to your account',
};

function LoginContent() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      {/* LoginForm dùng useSearchParams → bắt buộc bọc Suspense khi prerender tĩnh */}
      <Suspense fallback={null}>
        <LoginForm />
      </Suspense>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center px-4">Loading...</div>}>
      <LoginContent />
    </Suspense>
  );
}
