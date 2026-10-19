'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
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
import LoginGoogle from '@/app/auth/login/google-button';
import { authApi } from '@/apis/auth.api';
import { useAuthStore } from '@/stores/auth.store';
import { User } from '@/shared/types/api.types';
import { roleUtil } from '@/shared/utils/roleUtil';
import Spining from '@/components/loading/spining';
import Redirecting from '@/components/loading/redirecting';
import { parseAxiosError } from '@/lib/axiosClient';

const loginEmailPasswordSchema = z.object({
  username: z.email('Vui lòng nhập email hợp lệ'),
  password: z.string().min(6, 'Mật khẩu phải có ít nhất 6 ký tự'),
});

function LoginForm() {
  const searchParams = useSearchParams();
  const returnPage = searchParams.get('return-page') || null;
  const user = useAuthStore((state) => state.user);
  const [mounted, setMounted] = useState(false);

  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loginForm = useForm<z.infer<typeof loginEmailPasswordSchema>>({
    resolver: zodResolver(loginEmailPasswordSchema),
    mode: 'onChange',
    defaultValues: {
      username: 'tranthuyen2222@gmail.com',
      password: '123456',
    },
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (user) {
      router.push(returnPage || roleUtil.getHomeRouteByRole(user.roles));
    }
  }, [user, router]);

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

  const onSubmit = async (data: z.infer<typeof loginEmailPasswordSchema>) => {
    setError(null);
    const { username, password } = data;

    try {
      // API login
      const res = await authApi.login({ username, password });
      if (!res.success) {
        const errorMessage = res.message || 'Đăng nhập thất bại. Vui lòng thử lại.';
        setError(errorMessage);
        return;
      }

      if (!res.result.accessToken) {
        setError('Đăng nhập thất bại. Không nhận được access token.');
        return;
      }
      useAuthStore.getState().setAccessToken(res.result.accessToken);

      // API get me
      const meRes = await authApi.getMe();
      const user: User = meRes.result;
      if (!meRes.success || !meRes.result) {
        toast.error(
          'Đăng nhập thất bại.' + (meRes.message || 'Không thể lấy thông tin người dùng.'),
        );
        return;
      }
      useAuthStore.getState().setUser(meRes.result);

      // reset form
      reset({
        username: '',
        password: '',
      });

      toast.success((res.message || 'Đăng nhập thành công.') + 'Đang chuyển trang...', {
        duration: 900,
      });

      // chuyển trang theo role
      const toRoute = returnPage || roleUtil.getHomeRouteByRole(user.roles);
      router.push(toRoute);
    } catch (error: any) {
      const { statusCode, message } = parseAxiosError(error);
      setError('Lỗi khi đăng nhập. ' + message || 'Vui lòng thử lại.');
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">Đăng nhập</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form id="login-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* API err message */}
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
                    Tài khoản (Email)
                  </FieldLabel>
                  <Input
                    {...field}
                    id="username"
                    aria-invalid={fieldState.invalid}
                    placeholder="you@example.com"
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
                      placeholder="Enter password"
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

        <div className="text-center text-sm">
          <span className="text-muted-foreground">Đăng nhập bằng tài khoản khác</span>
        </div>
        <LoginGoogle />
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
