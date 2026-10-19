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
import { authApi } from '@/apis/auth.api';
import LoginGoogle from '@/app/auth/login/google-button';
import useAuthApi from '@/hooks/tankstack/useAuthApi';
import { parseAxiosError } from '@/lib/axiosClient';

export const signupWithEmailSchema = z
  .object({
    fullName: z
      .string()
      .min(5, 'Họ và tên phải có ít nhất 5 ký tự')
      .max(100, 'Họ và tên phải ngắn hơn 100 ký tự'),
    email: z.email('Địa chỉ email không hợp lệ'),
    password: z.string().min(6, 'Mật khẩu phải có ít nhất 6 ký tự'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Mật khẩu xác nhận không khớp',
    path: ['confirmPassword'],
  });

function SignUpForm() {
  const router = useRouter();

  // mutation
  const signupMutation = useAuthApi.useSignup();

  const {
    control,
    reset,
    handleSubmit,
    formState: { isValid, isSubmitting },
  } = useForm<z.infer<typeof signupWithEmailSchema>>({
    resolver: zodResolver(signupWithEmailSchema),
    mode: 'onChange',
    defaultValues: {
      fullName: 'Trần Minh Thuyên',
      email: 'tranthuyen2222@gmail.com',
      password: '123456',
      confirmPassword: '123456',
    },
  });
  const [showPassword, setShowPassword] = useState({
    password: false,
    confirmPassword: false,
  });
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (data: z.infer<typeof signupWithEmailSchema>) => {
    signupMutation.mutate(data, {
      onSuccess: (response) => {
        toast.success(
          response.message || 'Đăng ký thành công! Vui lòng kiểm tra email để xác minh.',
        );
        reset();
        router.push('/auth/login');
      },
      onError: (error: any) => {
        const parsedError = parseAxiosError(error);
        setError(parsedError.message || 'Đăng ký thất bại. Vui lòng thử lại.');
      },
    });
    setError(null);
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">Đăng ký tài khoản</CardTitle>
        <CardDescription>Bắt đầu hành trình khám phá phim</CardDescription>
      </CardHeader>
      <CardContent>
        <form
          id="signup-form"
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-2"
          suppressHydrationWarning={true}
        >
          {/* API err message */}
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
                    Full Name
                  </FieldLabel>
                  <Input
                    {...field}
                    id="fullName"
                    aria-invalid={fieldState.invalid}
                    placeholder="John Doe"
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
                    aria-invalid={fieldState.invalid}
                    placeholder="you@example.com"
                    autoComplete="email"
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
                    Password
                  </FieldLabel>
                  <InputGroup>
                    <InputGroupInput
                      {...field}
                      id="password"
                      type={showPassword.password ? 'text' : 'password'}
                      aria-invalid={fieldState.invalid}
                      placeholder="Enter password"
                      autoComplete="current-password"
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
                    Confirm Password
                  </FieldLabel>
                  <InputGroup>
                    <InputGroupInput
                      {...field}
                      id="confirmPassword"
                      type={showPassword.confirmPassword ? 'text' : 'password'}
                      aria-invalid={fieldState.invalid}
                      placeholder="Confirm password"
                      autoComplete="current-confirm-password"
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

        <div className="text-center text-sm">
          <span className="text-muted-foreground">Đăng nhập bằng tài khoản khác</span>
        </div>
        <LoginGoogle />
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
