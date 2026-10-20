import { Metadata } from 'next';
import SignUpForm from './signup-form';

export const metadata: Metadata = {
  title: 'Đăng ký | Legal AI',
  description: 'Tạo tài khoản mới để sử dụng hệ thống trợ đáp pháp lý Legal AI.',
};

export default function SignupPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <SignUpForm />
    </div>
  );
}
