import { cn } from '@/lib/utils';
import { Facebook, Github, Youtube } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import type { ReactNode } from 'react';

/**
 * Social links của website — **placeholder**: chủ website điền URL thật vào đây
 * (hiện project chưa có config env cho social, không bịa URL).
 */
const SOCIAL_LINKS = [
  { name: 'Facebook', href: '#', icon: Facebook },
  { name: 'YouTube', href: '#', icon: Youtube },
  { name: 'GitHub', href: '#', icon: Github },
] satisfies { name: string; href: string; icon: typeof Facebook }[];

const exploreLinks = [
  { name: 'Trang chủ', href: '/' },
  { name: 'Danh sách phim', href: '/movies' },
];

const infoLinks = [
  { name: 'Về chúng tôi', href: '/about' },
  { name: 'Liên hệ', href: '/contact' },
];

const legalLinks = [
  { name: 'Chính sách bảo mật', href: '/privacy' },
  { name: 'Điều khoản sử dụng', href: '/terms' },
];

function FooterLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link
      href={href}
      className="text-muted-foreground hover:text-foreground inline-flex text-sm transition-colors hover:underline"
    >
      {children}
    </Link>
  );
}

/**
 * Footer site-wide (thông tin website): giới thiệu, link nhanh, About/Contact,
 * chính sách, mạng xã hội, copyright. Hiển thị ở mọi trang `(main)` qua `UserLayout`.
 */
export function SiteFooter({ className }: { className?: string }) {
  return (
    <footer className={cn('border-t', className)}>
      <div className="mx-auto w-full max-w-7xl px-4 py-8 md:px-8">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {/* Giới thiệu */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2">
              <Image width={32} height={32} src="/logo2.png" alt="Logo" />
              <span className="text-lg font-bold text-gray-900 dark:text-white">Movie</span>
            </Link>
            <p className="text-muted-foreground mt-3 text-sm leading-relaxed">
              Ứng dụng gợi ý phim thông minh — khám phá, đánh giá và lưu giữ những bộ phim bạn yêu
              thích.
            </p>
            <div className="mt-4 flex items-center gap-3">
              {SOCIAL_LINKS.map((social) => (
                <a
                  key={social.name}
                  href={social.href}
                  aria-label={social.name}
                  title={social.name}
                  className="text-muted-foreground hover:text-foreground hover:bg-accent rounded-full p-2 transition-colors"
                >
                  <social.icon className="size-4" aria-hidden="true" />
                </a>
              ))}
            </div>
          </div>

          {/* Khám phá */}
          <nav aria-label="Khám phá">
            <h3 className="text-sm font-semibold">Khám phá</h3>
            <ul className="mt-3 space-y-2">
              {exploreLinks.map((link) => (
                <li key={link.href}>
                  <FooterLink href={link.href}>{link.name}</FooterLink>
                </li>
              ))}
            </ul>
          </nav>

          {/* Thông tin */}
          <nav aria-label="Thông tin">
            <h3 className="text-sm font-semibold">Thông tin</h3>
            <ul className="mt-3 space-y-2">
              {infoLinks.map((link) => (
                <li key={link.href}>
                  <FooterLink href={link.href}>{link.name}</FooterLink>
                </li>
              ))}
            </ul>
          </nav>

          {/* Pháp lý */}
          <nav aria-label="Pháp lý">
            <h3 className="text-sm font-semibold">Pháp lý</h3>
            <ul className="mt-3 space-y-2">
              {legalLinks.map((link) => (
                <li key={link.href}>
                  <FooterLink href={link.href}>{link.name}</FooterLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="border-border text-muted-foreground mt-8 border-t pt-6 text-center text-sm">
          © {new Date().getFullYear()} Movie Recommendation. Tất cả quyền được bảo lưu.
        </div>
      </div>
    </footer>
  );
}
