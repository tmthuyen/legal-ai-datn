import { PageHeader } from '@/components/common/PageHeader';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Liên hệ — Movie Recommendation',
};

export default function ContactPage() {
  return (
    <div className="w-full space-y-6 pb-10">
      <PageHeader title="Liên hệ" description="Kết nối với chúng tôi" />

      <div className="text-muted-foreground max-w-3xl space-y-4 text-sm leading-relaxed">
        <p>
          Chúng tôi luôn sẵn sàng lắng nghe góp ý, câu hỏi hoặc báo lỗi về website. Nếu bạn gặp vấn
          đề khi sử dụng hoặc có đề xuất cải thiện, hãy liên hệ với chúng tôi qua các kênh dưới đây.
        </p>

        <div className="bg-card space-y-3 rounded-xl border p-4">
          <div>
            <h2 className="text-foreground font-semibold">Email</h2>
            <p>Địa chỉ email liên hệ sẽ được cập nhật tại đây.</p>
          </div>
          <div>
            <h2 className="text-foreground font-semibold">Mạng xã hội</h2>
            <p>Các kênh mạng xã hội chính thức của website sẽ được cập nhật tại đây.</p>
          </div>
          <div>
            <h2 className="text-foreground font-semibold">Báo lỗi</h2>
            <p>
              Khi báo lỗi, vui lòng ghi rõ mô tả lỗi, các bước tái hiện và thông tin trình duyệt để
              chúng tôi hỗ trợ nhanh hơn.
            </p>
          </div>
        </div>

        <p className="text-muted-foreground/80 text-xs italic">
          * Thông tin liên hệ chi tiết do chủ website bổ sung.
        </p>
      </div>
    </div>
  );
}
