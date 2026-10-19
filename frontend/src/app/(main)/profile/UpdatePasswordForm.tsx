'use client';

import { authApi } from '@/apis/auth.api';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Field, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { InputGroup, InputGroupAddon, InputGroupInput } from '@/components/ui/input-group';
import { parseAxiosError } from '@/lib/axiosClient';
import { UpdatePasswordData } from '@/shared/types/api.types';
import { useAuthStore } from '@/stores/auth.store';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { EyeIcon, EyeOffIcon, KeyRound } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { toast } from 'sonner';
import z from 'zod';

const updatePasswordSchema = z.object({
  oldPassword: z.string().min(6, 'Mật khẩu phải cũ có ít nhất 6 ký tự'),
  newPassword: z.string().min(6, 'Mật khẩu phải mới có ít nhất 6 ký tự'),
  confirmPassword: z.string().min(6, 'Mật khẩu xác nhận phải có ít nhất 6 ký tự'),
});

export default function UpdatePasswordForm() {
  const router = useRouter();

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const updatePasswordForm = useForm<z.infer<typeof updatePasswordSchema>>({
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
  } = updatePasswordForm;

  // tanstack query mutation
  const passwordMutation = useMutation({
    mutationFn: (data: UpdatePasswordData) => authApi.updatePassword(data),
    onSuccess: () => {
      toast.success('Cập nhật mật khẩu thành công!');
      reset();

      // clear auth state
      useAuthStore.getState().clearAuth();

      // login again
      router.push('/auth/login?return-page=' + encodeURIComponent('profile'));
    },
    onError: (error: any) => {
      const { statusCode, message } = parseAxiosError(error);
      setError(message || 'Lỗi khi cập nhật mật khẩu. Vui lòng thử lại.');
      // toast.error(message);
    },
  });

  const onSubmitUpdatePassword = async (data: z.infer<typeof updatePasswordSchema>) => {
    setError(null);
    const { oldPassword, newPassword, confirmPassword } = data;

    if (newPassword !== confirmPassword) {
      setError('Mật khẩu xác nhận không khớp!');
      return;
    }

    return await passwordMutation.mutateAsync({ oldPassword, newPassword, confirmPassword });
  };

  return (
    <Card className="border border-gray-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <CardHeader className="bg-white pb-4 dark:bg-slate-900">
        <CardTitle className="flex items-center gap-2">
          <KeyRound className={`text-accent-foreground h-5 w-5`} /> Đổi Mật Khẩu
        </CardTitle>
        <CardDescription>Cập nhật mật khẩu để bảo vệ tài khoản của bạn tốt hơn.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4">
          <form
            id="update-password-form"
            onSubmit={handleSubmit(onSubmitUpdatePassword)}
            className="space-y-4"
          >
            {/* API err message */}
            {error && (
              <div className="text-destructive bg-destructive/10 border-destructive/20 rounded-lg border p-3 text-sm">
                {error}
              </div>
            )}
            <FieldGroup>
              <Controller
                name="oldPassword"
                control={control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="oldPassword" className="cursor-pointer">
                      Mật khẩu cũ
                    </FieldLabel>
                    <InputGroup>
                      <InputGroupInput
                        {...field}
                        id="oldPassword"
                        type={showPassword ? 'text' : 'password'}
                        aria-invalid={fieldState.invalid}
                        placeholder="Nhập mật khẩu cũ"
                        autoComplete="oldPassword"
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
              <Controller
                name="newPassword"
                control={control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="newPassword" className="cursor-pointer">
                      Mật khẩu mới
                    </FieldLabel>
                    <InputGroup>
                      <InputGroupInput
                        {...field}
                        id="newPassword"
                        type={showPassword ? 'text' : 'password'}
                        aria-invalid={fieldState.invalid}
                        placeholder="Nhập mật khẩu mới"
                        autoComplete="new-password"
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
                        type={showPassword ? 'text' : 'password'}
                        aria-invalid={fieldState.invalid}
                        placeholder="Nhập mật khẩu xác nhận"
                        autoComplete="new-password"
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
