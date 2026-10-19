import { PageHeader } from '@/components/common/PageHeader';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Chính sách bảo mật — Movie Recommendation',
};

export default function PrivacyPage() {
  return (
    <div className="w-full space-y-6 pb-10">
      <PageHeader
        title="Chính sách bảo mật"
        description="Cách chúng tôi thu thập và sử dụng thông tin của bạn"
      />

      <div className="text-muted-foreground max-w-3xl space-y-6 text-sm leading-relaxed">
        <section className="space-y-2">
          <h2 className="text-foreground text-base font-semibold">1. Thông tin thu thập</h2>
          <p>Khi bạn sử dụng website, chúng tôi có thể thu thập các thông tin sau:</p>
          <ul className="list-disc space-y-1 pl-6">
            <li>
              Thông tin tài khoản (họ tên, email, ảnh đại diện) khi bạn đăng ký hoặc đăng nhập.
            </li>
            <li>
              Dữ liệu tương tác: đánh giá, bình luận, phim yêu thích, lịch sử xem — dùng để cá nhân
              hoá gợi ý phim.
            </li>
            <li>Thông tin kỹ thuật cơ bản (trình duyệt, thiết bị) cho mục đích vận hành.</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-foreground text-base font-semibold">2. Mục đích sử dụng</h2>
          <ul className="list-disc space-y-1 pl-6">
            <li>Cung cấp và cải thiện trải nghiệm gợi ý phim phù hợp với bạn.</li>
            <li>Quản lý tài khoản, xác thực và bảo mật phiên đăng nhập.</li>
            <li>Hiển thị nội dung bạn đã tương tác (đánh giá, bình luận, danh sách yêu thích).</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-foreground text-base font-semibold">3. Chia sẻ thông tin</h2>
          <p>
            Chúng tôi không bán hoặc chia sẻ thông tin cá nhân của bạn cho bên thứ ba vì mục đích
            thương mại. Dữ liệu chỉ được sử dụng nội bộ cho mục đích vận hành và cá nhân hoá gợi ý.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-foreground text-base font-semibold">4. Bảo mật</h2>
          <p>
            Phiên đăng nhập được quản lý bằng cơ chế token; mật khẩu không được lưu ở dạng văn bản
            thuần. Chúng tôi không ngừng cải thiện các biện pháp bảo vệ dữ liệu người dùng.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-foreground text-base font-semibold">5. Quyền của bạn</h2>
          <p>
            Bạn có thể xem và cập nhật thông tin hồ sơ của mình bất cứ lúc nào. Nếu có câu hỏi về
            chính sách bảo mật, vui lòng truy cập trang{' '}
            <a href="/contact" className="text-primary underline">
              Liên hệ
            </a>
            .
          </p>
        </section>

        <p className="text-muted-foreground/80 text-xs italic">
          * Chính sách này là bản mô tả chung cho mục đích học tập của dự án; chủ website có thể bổ
          sung điều khoản chi tiết khi triển khai thật.
        </p>
      </div>
    </div>
  );
}
