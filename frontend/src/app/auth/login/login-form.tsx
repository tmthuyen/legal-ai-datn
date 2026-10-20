'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { toast } from 'sonner';
import z from 'zod';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Field, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field';
import { InputGroup, InputGroupAddon, InputGroupInput } from '@/components/ui/input-group';
import { EyeIcon, EyeOffIcon } from 'lucide-react';
import { legalAuthApi } from '@/apis/legal.api';
import { useAuthStore } from '@/stores/auth.store';
import { LegalUser } from '@/shared/types/legal.types';
import { roleUtil } from '@/shared/utils/roleUtil';
import Spining from '@/components/loading/spining';
import Redirecting from '@/components/loading/redirecting';
import { parseAxiosError } from '@/lib/axiosClient';

// Contract `POST /auth/login` nhận `username` (không phải email) + mật khẩu tối thiểu 8 ký tự.
const loginSchema = z.object({
  username: z.string().min(3, 'Tên đăng nhập phải có ít nhất 3 ký tự'),
  password: z.string().min(8, 'Mật khẩu phải có ít nhất 8 ký tự'),
});

function LoginForm() {
  const searchParams = useSearchParams();
  const returnPage = searchParams.get('return-page') || null;
  const user = useAuthStore((state) => state.user);
  const [mounted, setMounted] = useState(false);

  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loginForm = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    mode: 'onChange',
    defaultValues: {
      username: '',
      password: '',
    },
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (user) {
      router.push(returnPage || roleUtil.getHomeRouteByRole(user));
    }
  }, [user, router, returnPage]);

  if (!mounted) {
    return <Spining />;
  }

  if (user) {
    return <Redirecting />;
  }

  const {
    control,
    reset,
    handleSubmit,
    formState: { isValid, isSubmitting },
  } = loginForm;

  const onSubmit = async (data: z.infer<typeof loginSchema>) => {
    setError(null);
    const { username, password } = data;

    try {
      // POST /auth/login → { accessToken, user }
      const res = await legalAuthApi.login({ username, password });
      if (!res.success || !res.result?.accessToken) {
        setError(res.message || 'Đăng nhập thất bại. Vui lòng thử lại.');
        return;
      }
      useAuthStore.getState().setAccessToken(res.result.accessToken);

      // GET /auth/me — lấy profile hiện tại (nguồn sự thật cho quyền/role).
      const meRes = await legalAuthApi.getMe();
      const me: LegalUser | undefined = meRes.result;
      if (!meRes.success || !me) {
        setError(meRes.message || 'Không thể lấy thông tin người dùng.');
        return;
      }
      useAuthStore.getState().setUser(me);

      reset({ username: '', password: '' });

      toast.success(res.message || 'Đăng nhập thành công.', { duration: 900 });

      const toRoute = returnPage || roleUtil.getHomeRouteByRole(me);
      router.push(toRoute);
    } catch (err: unknown) {
      const { message } = parseAxiosError(err);
      setError(message || 'Lỗi khi đăng nhập. Vui lòng thử lại.');
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">Đăng nhập</CardTitle>
        <CardDescription>Truy cập hệ thống trợ đáp pháp lý Legal AI</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form id="login-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Thông báo lỗi lấy từ envelope error */}
          {error && (
            <div className="text-destructive bg-destructive/10 border-destructive/20 rounded-lg border p-3 text-sm">
              {error}
            </div>
          )}
          <FieldGroup>
            <Controller
              name="username"
              control={control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="username" className="cursor-pointer">
                    Tên đăng nhập
                  </FieldLabel>
                  <Input
                    {...field}
                    id="username"
                    aria-invalid={fieldState.invalid}
                    placeholder="Tên đăng nhập của bạn"
                    autoComplete="username"
                  />
                  {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                </Field>
              )}
            />
            <Controller
              name="password"
              control={control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="password" className="cursor-pointer">
                    Mật khẩu
                  </FieldLabel>
                  <InputGroup>
                    <InputGroupInput
                      {...field}
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      aria-invalid={fieldState.invalid}
                      placeholder="Nhập mật khẩu"
                      autoComplete="current-password"
                    />
                    <InputGroupAddon
                      align="inline-end"
                      className="cursor-pointer"
                      onClick={() => {
                        setShowPassword((prev) => !prev);
                      }}
                    >
                      {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                    </InputGroupAddon>
                  </InputGroup>
                  {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                </Field>
              )}
            />
          </FieldGroup>
        </form>
        <Button
          type="submit"
          form="login-form"
          className={`mt-4 w-full shadow-lg ${!isValid || isSubmitting ? 'opacity-50' : 'cursor-pointer'}`}
          disabled={!isValid || isSubmitting}
        >
          {isSubmitting ? 'Đang đăng nhập...' : 'Đăng nhập'}
        </Button>
      </CardContent>

      <CardFooter className="flex-col text-center">
        <div className="text-center text-sm">
          <span className="text-muted-foreground">Chưa có tài khoản? </span>
          <Link href="/auth/signup" className="text-primary font-medium hover:underline">
            Đăng ký
          </Link>
        </div>
      </CardFooter>
    </Card>
  );
}

export default LoginForm;
