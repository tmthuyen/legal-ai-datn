import { Metadata } from 'next';
import SignUpForm from './signup-form';

export const metadata: Metadata = {
  title: 'Đăng ký | Movie Recommendation',
  description:
    'Tạo tài khoản mới để truy cập vào Movie Recommendation và khám phá các bộ phim yêu thích của bạn.',
};

export default function SignupPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <SignUpForm />
    </div>
  );
}
