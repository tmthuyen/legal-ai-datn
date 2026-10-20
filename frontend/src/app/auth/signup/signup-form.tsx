'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
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
import { parseAxiosError } from '@/lib/axiosClient';
import { roleUtil } from '@/shared/utils/roleUtil';

// Contract `POST /auth/register`: email hợp lệ, username 3–50 ký tự, password ≥ 8, fullName tùy chọn.
const signupSchema = z
  .object({
    fullName: z.string().max(255, 'Họ tên tối đa 255 ký tự').optional(),
    email: z.email('Địa chỉ email không hợp lệ'),
    username: z
      .string()
      .min(3, 'Tên đăng nhập phải có ít nhất 3 ký tự')
      .max(50, 'Tên đăng nhập tối đa 50 ký tự'),
    password: z.string().min(8, 'Mật khẩu phải có ít nhất 8 ký tự'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Mật khẩu xác nhận không khớp',
    path: ['confirmPassword'],
  });

function SignUpForm() {
  const router = useRouter();

  const {
    control,
    reset,
    handleSubmit,
    formState: { isValid, isSubmitting },
  } = useForm<z.infer<typeof signupSchema>>({
    resolver: zodResolver(signupSchema),
    mode: 'onChange',
    defaultValues: {
      fullName: '',
      email: '',
      username: '',
      password: '',
      confirmPassword: '',
    },
  });
  const [showPassword, setShowPassword] = useState({
    password: false,
    confirmPassword: false,
  });
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (data: z.infer<typeof signupSchema>) => {
    setError(null);
    try {
      const res = await legalAuthApi.register({
        email: data.email,
        username: data.username,
        password: data.password,
        fullName: data.fullName || undefined,
      });

      if (!res.success) {
        setError(res.message || 'Đăng ký thất bại. Vui lòng thử lại.');
        return;
      }

      // Đăng ký thành công trả `AuthResult` → đăng nhập luôn.
      if (res.result?.accessToken && res.result.user) {
        useAuthStore.getState().setAccessToken(res.result.accessToken);
        useAuthStore.getState().setUser(res.result.user);
        toast.success(res.message || 'Đăng ký thành công!', { duration: 900 });
        reset();
        router.push(roleUtil.getHomeRouteByRole(res.result.user));
        return;
      }

      toast.success(res.message || 'Đăng ký thành công! Vui lòng đăng nhập.');
      reset();
      router.push('/auth/login');
    } catch (err: unknown) {
      const { message } = parseAxiosError(err);
      setError(message || 'Đăng ký thất bại. Vui lòng thử lại.');
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">Đăng ký tài khoản</CardTitle>
        <CardDescription>Bắt đầu hỏi đáp pháp luật cùng Legal AI</CardDescription>
      </CardHeader>
      <CardContent>
        <form
          id="signup-form"
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-2"
          suppressHydrationWarning={true}
        >
          {/* Thông báo lỗi lấy từ envelope error */}
          {error && (
            <div className="text-destructive bg-destructive/10 border-destructive/20 rounded-lg border p-3 text-sm">
              {error}
            </div>
          )}
          <FieldGroup className="gap-2">
            <Controller
              control={control}
              name="fullName"
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="fullName" className="cursor-pointer">
                    Họ và tên
                  </FieldLabel>
                  <Input
                    {...field}
                    id="fullName"
                    aria-invalid={fieldState.invalid}
                    placeholder="Nguyễn Văn A"
                    autoComplete="name"
                  />
                  {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                </Field>
              )}
            />

            <Controller
              name="email"
              control={control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="email" className="cursor-pointer">
                    Email
                  </FieldLabel>
                  <Input
                    {...field}
                    id="email"
                    type="email"
                    aria-invalid={fieldState.invalid}
                    placeholder="you@example.com"
                    autoComplete="email"
                  />
                  {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                </Field>
              )}
            />

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
                    placeholder="Tên đăng nhập (3–50 ký tự)"
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
                      type={showPassword.password ? 'text' : 'password'}
                      aria-invalid={fieldState.invalid}
                      placeholder="Tối thiểu 8 ký tự"
                      autoComplete="new-password"
                    />
                    <InputGroupAddon
                      align="inline-end"
                      className="cursor-pointer"
                      onClick={() => {
                        setShowPassword((prev) => ({ ...prev, password: !prev.password }));
                      }}
                    >
                      {showPassword.password ? <EyeOffIcon /> : <EyeIcon />}
                    </InputGroupAddon>
                  </InputGroup>
                  {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                </Field>
              )}
            />
            <Controller
              name="confirmPassword"
              control={control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="confirmPassword" className="cursor-pointer">
                    Xác nhận mật khẩu
                  </FieldLabel>
                  <InputGroup>
                    <InputGroupInput
                      {...field}
                      id="confirmPassword"
                      type={showPassword.confirmPassword ? 'text' : 'password'}
                      aria-invalid={fieldState.invalid}
                      placeholder="Nhập lại mật khẩu"
                      autoComplete="new-password"
                    />
                    <InputGroupAddon
                      align="inline-end"
                      className="cursor-pointer"
                      onClick={() => {
                        setShowPassword((prev) => ({
                          ...prev,
                          confirmPassword: !prev.confirmPassword,
                        }));
                      }}
                    >
                      {showPassword.confirmPassword ? <EyeOffIcon /> : <EyeIcon />}
                    </InputGroupAddon>
                  </InputGroup>
                  {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                </Field>
              )}
            />
          </FieldGroup>
        </form>
      </CardContent>

      <CardFooter className="flex-col gap-4 text-center">
        <Button
          type="submit"
          form="signup-form"
          className="w-full"
          disabled={!isValid || isSubmitting}
        >
          {isSubmitting ? 'Đang đăng ký...' : 'Đăng ký'}
        </Button>

        <div className="mt-4 text-center text-sm">
          <span className="text-muted-foreground">Đã có tài khoản? </span>
          <Link href="/auth/login" className="text-primary font-medium hover:underline">
            Đăng nhập
          </Link>
        </div>
      </CardFooter>
    </Card>
  );
}
export default SignUpForm;
