import { PageHeader } from '@/components/common/PageHeader';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Điều khoản sử dụng — Movie Recommendation',
};

export default function TermsPage() {
  return (
    <div className="w-full space-y-6 pb-10">
      <PageHeader
        title="Điều khoản sử dụng"
        description="Các điều kiện khi sử dụng Movie Recommendation"
      />

      <div className="text-muted-foreground max-w-3xl space-y-6 text-sm leading-relaxed">
        <section className="space-y-2">
          <h2 className="text-foreground text-base font-semibold">1. Chấp nhận điều khoản</h2>
          <p>
            Khi truy cập và sử dụng website, bạn đồng ý tuân thủ các điều khoản sử dụng này. Nếu
            không đồng ý, vui lòng không sử dụng các tính năng của website.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-foreground text-base font-semibold">2. Tài khoản người dùng</h2>
          <ul className="list-disc space-y-1 pl-6">
            <li>Bạn cần đăng nhập để sử dụng các tính năng tương tác (đánh giá, bình luận…).</li>
            <li>Bạn chịu trách nhiệm bảo mật thông tin đăng nhập của mình.</li>
            <li>
              Không đăng tải nội dung vi phạm pháp luật, xâm phạm quyền lợi hoặc gây ảnh hưởng xấu
              đến người khác.
            </li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-foreground text-base font-semibold">3. Nội dung do người dùng tạo</h2>
          <p>
            Bình luận và đánh giá do bạn đăng tải chịu trách nhiệm pháp lý bởi chính bạn. Chúng
            tôi có thể gỡ bỏ nội dung vi phạm mà không cần báo trước.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-foreground text-base font-semibold">4. Giới hạn trách nhiệm</h2>
          <p>
            Website được cung cấp ở trạng thái &quot;nguyên trạng&quot; cho mục đích học tập và nghiên
            cứu. Chúng tôi không đảm bảo website không gián đoạn hoặc không có lỗi.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-foreground text-base font-semibold">5. Thay đổi điều khoản</h2>
          <p>
            Các điều khoản có thể được cập nhật theo thời gian. Việc tiếp tục sử dụng website sau
            thay đổi đồng nghĩa với việc bạn chấp nhận điều khoản mới. Câu hỏi vui lòng xem trang{' '}
            <a href="/contact" className="text-primary underline">
              Liên hệ
            </a>
            .
          </p>
        </section>

        <p className="text-muted-foreground/80 text-xs italic">
          * Điều khoản này là bản mô tả chung cho mục đích học tập của dự án; chủ website có thể bổ
          sung điều khoản chi tiết khi triển khai thật.
        </p>
      </div>
    </div>
  );
}
