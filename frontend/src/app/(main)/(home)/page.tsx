import type { Metadata } from 'next';
import Link from 'next/link';
import {
  ArrowRight,
  BookOpenCheck,
  FileText,
  MessagesSquare,
  Network,
  Scale,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export const metadata: Metadata = {
  title: 'Legal AI — Trợ đáp pháp lý Việt Nam',
  description:
    'Hệ thống hỏi đáp pháp luật Việt Nam dựa trên Knowledge Graph & suy luận phản thực (GraphRAG).',
};

/** Corpus giới hạn 5 văn bản theo phạm vi đồ án. */
const CORPUS = [
  { code: 'Hiến pháp 2013', note: 'Luật cơ bản của Nhà nước' },
  { code: 'Bộ luật Dân sự 2015', note: 'Quan hệ dân sự, tài sản, thừa kế' },
  { code: 'Nghị định 21/2021/NĐ-CP', note: 'Bảo đảm thực hiện nghĩa vụ' },
  { code: 'Nghị định 19/2019/NĐ-CP', note: 'Họ, hụi, biêu, phường' },
  { code: 'Nghị quyết 02/2022/NQ-HĐTP', note: 'Án lệ, hướng dẫn áp dụng' },
];

const FEATURES = [
  {
    icon: MessagesSquare,
    title: 'Hỏi đáp pháp luật',
    description:
      'Đặt câu hỏi bằng tiếng Việt tự nhiên, nhận câu trả lời tổng hợp kèm trích dẫn Điều/Khoản/Điểm liên quan.',
  },
  {
    icon: Network,
    title: 'Knowledge Graph pháp lý',
    description:
      'Đồ thị phân cấp Văn bản → Phần → Chương → Mục → Điều → Khoản → Điểm, liên kết tham chiếu giữa các điều luật.',
  },
  {
    icon: BookOpenCheck,
    title: 'Trích dẫn minh bạch',
    description:
      'Mỗi câu trả lời đều kèm phân cấp luật trích xuất và danh sách điều luật liên quan để đối chiếu.',
  },
  {
    icon: ShieldCheck,
    title: 'Lưu lịch sử hội thoại',
    description:
      'Quản lý nhiều cuộc hội thoại, xem lại toàn bộ câu hỏi và câu trả lời bất cứ lúc nào.',
  },
];

export default function HomePage() {
  return (
    <div className="animate-fade-in w-full space-y-12 pb-12">
      {/* Hero */}
      <section className="from-primary/10 via-primary/5 to-background relative overflow-hidden rounded-2xl border bg-gradient-to-br">
        <div className="grid gap-8 p-6 md:grid-cols-2 md:p-10">
          <div className="flex flex-col justify-center gap-5">
            <Badge variant="secondary" className="w-fit">
              <Sparkles className="size-3" aria-hidden /> GraphRAG · Legal Reasoning
            </Badge>
            <div className="space-y-3">
              <h1 className="text-3xl font-extrabold tracking-tight md:text-4xl lg:text-5xl">
                Trợ lý pháp lý Việt Nam dựa trên tri thức
              </h1>
              <p className="text-muted-foreground max-w-xl text-lg">
                Đặt câu hỏi về Hiến pháp, Bộ luật Dân sự và các nghị định, nghị quyết liên quan. Hệ
                thống truy xuất đồ thị tri thức và suy luận để trả lời kèm trích dẫn điều luật.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link href="/chat">
                  <MessagesSquare className="mr-2 size-4" />
                  Bắt đầu hỏi đáp
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/auth/signup">
                  Tạo tài khoản <ArrowRight className="ml-2 size-4" />
                </Link>
              </Button>
            </div>
          </div>

          <div className="flex items-center justify-center">
            <Card className="bg-background/70 w-full max-w-md backdrop-blur">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Scale className="text-primary size-5" aria-hidden />
                  Câu hỏi ví dụ
                </CardTitle>
                <CardDescription>Gợi ý nội dung bạn có thể tra cứu</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {[
                  'Điều 1 Hiến pháp 2013 quy định gì?',
                  'Thừa kế theo pháp luật được chia như thế nào?',
                  'Quy định về bảo đảm thực hiện nghĩa vụ theo NĐ 21/2021?',
                  'Họ, hụi, biêu, phường được pháp luật điều chỉnh ra sao?',
                ].map((question) => (
                  <Link
                    key={question}
                    href="/chat"
                    className="bg-muted/60 hover:bg-muted flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-sm transition-colors"
                  >
                    <span className="flex items-center gap-2">
                      <FileText className="text-muted-foreground size-4" aria-hidden />
                      {question}
                    </span>
                    <ArrowRight className="text-muted-foreground size-4 shrink-0" aria-hidden />
                  </Link>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Tính năng */}
      <section className="space-y-6">
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight">Hệ thống hoạt động như thế nào</h2>
          <p className="text-muted-foreground">
            Knowledge Graph + suy luận phản thực giúp câu trả lời bám sát quy định pháp luật.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature) => (
            <Card key={feature.title} className="h-full">
              <CardHeader>
                <div className="bg-primary/10 text-primary mb-2 flex size-10 items-center justify-center rounded-lg">
                  <feature.icon className="size-5" aria-hidden />
                </div>
                <CardTitle className="text-base">{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      {/* Corpus */}
      <section className="space-y-6">
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight">Phạm vi văn bản pháp luật</h2>
          <p className="text-muted-foreground">
            Hệ thống hiện hỏi đáp trong phạm vi 5 văn bản sau:
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CORPUS.map((doc) => (
            <Card key={doc.code}>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Scale className="text-primary size-4" aria-hidden />
                  <CardTitle className="text-base">{doc.code}</CardTitle>
                </div>
                <CardDescription>{doc.note}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="from-primary/15 via-primary/5 to-background flex flex-col items-center gap-4 rounded-2xl border bg-gradient-to-br p-8 text-center">
        <h2 className="text-2xl font-bold tracking-tight">Sẵn sàng tra cứu pháp luật?</h2>
        <p className="text-muted-foreground max-w-xl">
          Đăng nhập để lưu lịch sử hội thoại và nhận câu trả lời kèm trích dẫn điều luật đầy đủ.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Button asChild size="lg">
            <Link href="/chat">
              <MessagesSquare className="mr-2 size-4" />
              Vào phòng hỏi đáp
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/about">Tìm hiểu thêm</Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
