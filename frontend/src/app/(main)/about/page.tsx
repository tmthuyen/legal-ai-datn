import { PageHeader } from '@/components/common/PageHeader';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Về chúng tôi — Movie Recommendation',
};

export default function AboutPage() {
  return (
    <div className="w-full space-y-6 pb-10">
      <PageHeader
        title="Về chúng tôi"
        description="Giới thiệu về Movie Recommendation"
      />

      <div className="text-muted-foreground max-w-3xl space-y-4 text-sm leading-relaxed">
        <p>
          <strong className="text-foreground">Movie Recommendation</strong> là ứng dụng gợi ý phim
          được xây dựng với công nghệ LLM (Large Language Model) — kết hợp tìm kiếm ngữ nghĩa tiếng
          Việt và mô hình Collaborative Filtering (ALS) để gợi ý phim phù hợp với sở thích của từng
          người dùng.
        </p>
        <p>Với Movie Recommendation, bạn có thể:</p>
        <ul className="list-disc space-y-1 pl-6">
          <li>Khám phá phim theo tên, thể loại và quốc gia.</li>
          <li>Xem gợi ý phim cá nhân hoá dựa trên lịch sử xem và sở thích.</li>
          <li>Đánh giá sao, bình luận và thảo luận về bộ phim mình yêu thích.</li>
          <li>Lưu danh sách phim yêu thích và theo dõi lịch sử xem.</li>
        </ul>
        <p>
          Đây là sản phẩm phục vụ mục đích học tập và nghiên cứu về ứng dụng mô hình ngôn ngữ vào
          hệ thống gợi ý phim.
        </p>
      </div>
    </div>
  );
}
