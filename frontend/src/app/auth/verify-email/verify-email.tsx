'use client';

import { Button } from '@/components/ui/button';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, Check, RefreshCcw, RefreshCcwDot, X } from 'lucide-react';
import { useAuthStore } from '@/stores/auth.store';
import useAuthApi from '@/hooks/tankstack/useAuthApi';

export default function VerifyEmail() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const router = useRouter();

  const [isError, setIsError] = useState(false);

  // mutation to verify email
  const isCalled = useRef(false);
  const { mutate } = useAuthApi.useVerifyEmail();

  // verify email when token is available
  useEffect(() => {
    if (!token) {
      setIsError(true);
      return;
    }

    if (isCalled.current) return;

    isCalled.current = true;

    mutate(token, {
      onSuccess: (data) => {
        setIsError(false);
      },
      onError: (error: any) => {
        setIsError(true);
      },
    });
  }, [token, mutate]);

  return <>{isError ? <FailedVerifyEmail /> : <SuccessVerifyEmail />}</>;
}

function FailedVerifyEmail() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.isLoading);

  const [resending, setResending] = useState(false);

  const sendVerificationEmailMutation = useAuthApi.useSendVerificationEmail();
  const handleSendVerificationEmail = async () => {
    setResending(true);
    await sendVerificationEmailMutation.mutateAsync();
    setResending(false);
  };

  return (
    <Card className="w-full max-w-md shadow-xl">
      <CardHeader className="space-y-1">
        <CardTitle className="text-destructive flex flex-col items-center justify-center gap-4 text-2xl font-bold">
          <div className="bg-destructive/10 text-destructive flex h-16 w-16 items-center justify-center rounded-full">
            <X className="h-1/2 w-1/2" />
          </div>
          <div className="mx-auto">
            <h2 className="text-2xl">Xác thực email thất bại</h2>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="">
        <CardDescription className="text-muted-foreground text-center text-sm">
          Liên kết này không hợp lệ, đã được sử dụng, hoặc đã quá 24 giờ. Vui lòng yêu cầu gửi lại
          email xác minh từ trang tài khoản.
        </CardDescription>
      </CardContent>

      <CardFooter className="flex flex-col gap-2 text-center">
        {isAuthenticated && (
          <Button className="w-full" onClick={handleSendVerificationEmail} disabled={resending}>
            <RefreshCcw /> Gửi lại email xác minh
          </Button>
        )}

        {isLoading && (
          <Button className="w-full" disabled>
            <RefreshCcwDot /> Đang tải...
          </Button>
        )}

        {!isAuthenticated && !isLoading && (
          <Link href="/auth/login" className="w-full">
            <Button className="w-full">
              <ArrowLeft /> Quay lại trang đăng nhập
            </Button>
          </Link>
        )}
      </CardFooter>
    </Card>
  );
}

function SuccessVerifyEmail() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.isLoading);

  return (
    <Card className="w-full max-w-md shadow-xl">
      <CardHeader className="space-y-1">
        <CardTitle className="flex flex-col items-center justify-center gap-4 text-2xl font-bold text-green-300">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-300/10 text-green-300">
            <Check className="h-1/2 w-1/2" />
          </div>
          <div className="mx-auto">
            <h2 className="text-2xl">Xác thực email thành công</h2>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="">
        <CardDescription className="text-muted-foreground text-center text-sm">
          Email của bạn đã được xác thực thành công. Bạn có thể đăng nhập ngay bây giờ.
        </CardDescription>
      </CardContent>

      <CardFooter className="flex flex-col gap-2 text-center">
        {isAuthenticated && (
          <Link href="/" className="w-full">
            <Button className="w-full">
              <RefreshCcw /> Quay lại trang chủ
            </Button>
          </Link>
        )}

        {isLoading && (
          <Button className="w-full" disabled>
            <RefreshCcwDot /> Đang tải...
          </Button>
        )}

        {!isAuthenticated && !isLoading && (
          <Link href="/auth/login" className="w-full">
            <Button className="w-full">
              <ArrowLeft /> Quay lại trang đăng nhập
            </Button>
          </Link>
        )}
      </CardFooter>
    </Card>
  );
}
