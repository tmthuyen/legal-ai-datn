import { PageHeader } from '@/components/common/PageHeader';
import { ProfileForm } from './ProfileForm';

export const metadata = {
  title: 'Hồ sơ cá nhân',
  description:
    'Trang thông tin cá nhân của người dùng, nơi hiển thị các thông tin liên quan đến tài khoản và cài đặt cá nhân.',
};

export default function ProfilePage() {
  return (
    <>
      <div className="animate-fade-in w-full space-y-6 pb-10">
        <PageHeader title={metadata.title} description={metadata.description} />

        <ProfileForm metadata={metadata} />
      </div>
    </>
  );
}
