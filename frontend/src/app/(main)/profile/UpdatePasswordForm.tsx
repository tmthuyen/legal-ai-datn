'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Field, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field';
import { InputGroup, InputGroupAddon, InputGroupInput } from '@/components/ui/input-group';
import { useUpdatePassword } from '@/hooks/tankstack/useProfile';
import { useAuthStore } from '@/stores/auth.store';
import { zodResolver } from '@hookform/resolvers/zod';
import { EyeIcon, EyeOffIcon, KeyRound } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Controller, useForm } from 'react-hook-form';
import z from 'zod';

/**
 * Đổi mật khẩu theo contract §4.2 (`PUT /user/password`): chỉ gửi `oldPassword` + `newPassword`.
 * `confirmPassword` chỉ dùng để kiểm tra phía client, không gửi lên server.
 */
const updatePasswordSchema = z
  .object({
    oldPassword: z.string().min(8, 'Mật khẩu cũ phải có ít nhất 8 ký tự'),
    newPassword: z.string().min(8, 'Mật khẩu mới phải có ít nhất 8 ký tự'),
    confirmPassword: z.string().min(8, 'Mật khẩu xác nhận phải có ít nhất 8 ký tự'),
  })
  .refine((values) => values.newPassword === values.confirmPassword, {
    message: 'Mật khẩu xác nhận không khớp',
    path: ['confirmPassword'],
  });

export default function UpdatePasswordForm() {
  const router = useRouter();
  const updatePassword = useUpdatePassword();

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<z.infer<typeof updatePasswordSchema>>({
    resolver: zodResolver(updatePasswordSchema),
    mode: 'onChange',
    defaultValues: {
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
    },
  });

  const {
    control,
    reset,
    handleSubmit,
    formState: { isValid, isSubmitting },
  } = form;

  const onSubmit = async (data: z.infer<typeof updatePasswordSchema>) => {
    setError(null);
    try {
      await updatePassword.mutateAsync({
        oldPassword: data.oldPassword,
        newPassword: data.newPassword,
      });
      reset();
      // Vô hiệu hoá phiên hiện tại và yêu cầu đăng nhập lại bằng mật khẩu mới.
      await useAuthStore.getState().logout();
      router.push('/auth/login');
    } catch {
      setError('Không thể đổi mật khẩu. Vui lòng kiểm tra mật khẩu cũ và thử lại.');
    }
  };

  const passwordFields = (
    [
      { name: 'oldPassword', label: 'Mật khẩu cũ', placeholder: 'Nhập mật khẩu cũ', autoComplete: 'current-password' },
      { name: 'newPassword', label: 'Mật khẩu mới', placeholder: 'Nhập mật khẩu mới', autoComplete: 'new-password' },
      { name: 'confirmPassword', label: 'Xác nhận mật khẩu', placeholder: 'Nhập lại mật khẩu mới', autoComplete: 'new-password' },
    ] as const
  ).map((item) => (
    <Controller
      key={item.name}
      name={item.name}
      control={control}
      render={({ field, fieldState }) => (
        <Field data-invalid={fieldState.invalid}>
          <FieldLabel htmlFor={item.name} className="cursor-pointer">
            {item.label}
          </FieldLabel>
          <InputGroup>
            <InputGroupInput
              {...field}
              id={item.name}
              type={showPassword ? 'text' : 'password'}
              aria-invalid={fieldState.invalid}
              placeholder={item.placeholder}
              autoComplete={item.autoComplete}
            />
            <InputGroupAddon
              align="inline-end"
              className="cursor-pointer"
              onClick={() => setShowPassword((prev) => !prev)}
            >
              {showPassword ? <EyeOffIcon /> : <EyeIcon />}
            </InputGroupAddon>
          </InputGroup>
          {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
        </Field>
      )}
    />
  ));

  return (
    <Card className="border border-gray-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <CardHeader className="bg-white pb-4 dark:bg-slate-900">
        <CardTitle className="flex items-center gap-2">
          <KeyRound className="text-accent-foreground h-5 w-5" /> Đổi Mật Khẩu
        </CardTitle>
        <CardDescription>Cập nhật mật khẩu để bảo vệ tài khoản của bạn tốt hơn.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4">
          <form id="update-password-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && (
              <div className="text-destructive bg-destructive/10 border-destructive/20 rounded-lg border p-3 text-sm">
                {error}
              </div>
            )}
            <FieldGroup>{passwordFields}</FieldGroup>
          </form>
          <Button
            type="submit"
            form="update-password-form"
            variant="outline"
            className={`border-accent-foreground text-accent-foreground ms-auto border shadow-lg ${!isValid || isSubmitting ? 'opacity-50' : 'cursor-pointer'}`}
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? 'Đang cập nhật...' : 'Cập nhật mật khẩu'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
