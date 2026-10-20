'use client';

import { useState } from 'react';
import { Loader2, Mail, Save, ShieldCheck, User as UserIcon, UserCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Field, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useUpdateProfile } from '@/hooks/tankstack/useProfile';
import { useAuthStore } from '@/stores/auth.store';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import z from 'zod';

/**
 * Form cập nhật hồ sơ theo contract §4.2 — chỉ gửi các field được phép (`fullName`, `avatarUrl`).
 * Các field movie-era (gender/birthDate/phone/preferenceData/roles/status) không tồn tại
 * trong `LegalUser` nên không được hiển thị.
 */
const updateProfileSchema = z.object({
  fullName: z
    .string()
    .min(1, 'Tên hiển thị không được để trống')
    .max(50, 'Tên hiển thị không được quá 50 ký tự'),
  avatarUrl: z
    .string()
    .optional()
    .refine((value) => !value || /^https?:\/\//.test(value), 'URL ảnh không hợp lệ'),
});

type UpdateProfileForm = z.infer<typeof updateProfileSchema>;

export default function UserProfileForm() {
  const user = useAuthStore((state) => state.user);
  const updateProfile = useUpdateProfile();
  const [error, setError] = useState<string | null>(null);

  const form = useForm<UpdateProfileForm>({
    resolver: zodResolver(updateProfileSchema),
    mode: 'onChange',
    defaultValues: {
      fullName: user?.fullName ?? '',
      avatarUrl: user?.avatarUrl ?? undefined,
    },
  });

  const {
    control,
    handleSubmit,
    formState: { isValid, isSubmitting },
  } = form;

  const onSubmit = async (data: UpdateProfileForm) => {
    setError(null);
    try {
      await updateProfile.mutateAsync({
        fullName: data.fullName,
        avatarUrl: data.avatarUrl || undefined,
      });
      await useAuthStore.getState().refreshUser();
    } catch {
      setError('Không thể cập nhật hồ sơ. Vui lòng kiểm tra lại thông tin.');
    }
  };

  const initial = (user?.fullName ?? user?.username ?? 'U').charAt(0).toUpperCase();

  return (
    <Card className="w-full overflow-hidden border-gray-200 bg-white shadow-lg dark:border-slate-800 dark:bg-slate-900">
      <CardHeader>
        <div className="flex flex-col items-center justify-center gap-2">
          <FieldLabel className="me-auto text-lg">Ảnh đại diện</FieldLabel>
          <Avatar className="h-24 w-24">
            <AvatarImage src={user?.avatarUrl ?? undefined} alt={user?.fullName ?? 'Người dùng'} />
            <AvatarFallback>{initial}</AvatarFallback>
          </Avatar>
          <p className="text-muted-foreground text-xs">
            Nhập URL ảnh (http/https) ở trường bên dưới để cập nhật ảnh đại diện.
          </p>
        </div>
        <Separator className="my-2" />
      </CardHeader>
      <CardContent className="pt-0">
        <div className="mb-4 flex flex-col gap-3">
          <Field>
            <FieldLabel>
              <UserCheck className="h-4 w-4" /> Trạng thái tài khoản
            </FieldLabel>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={user?.isActive ? 'default' : 'destructive'}>
                {user?.isActive ? 'Đang hoạt động' : 'Đã khóa'}
              </Badge>
            </div>
          </Field>
          <Field>
            <FieldLabel>
              <ShieldCheck className="h-4 w-4" /> Vai trò
            </FieldLabel>
            <div className="flex flex-row flex-wrap gap-2">
              <Badge variant={user?.role === 'admin' ? 'destructive' : 'secondary'} className="uppercase">
                {user?.role ?? 'user'}
              </Badge>
            </div>
          </Field>
        </div>

        <Separator className="my-4" />

        <div className="flex flex-col gap-4">
          <form id="update-profile-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && (
              <div className="text-destructive bg-destructive/10 border-destructive/20 rounded-lg border p-3 text-sm">
                {error}
              </div>
            )}
            <FieldGroup className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Controller
                name="fullName"
                control={control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="fullName" className="cursor-pointer">
                      <UserIcon className="h-4 w-4" /> Tên hiển thị
                    </FieldLabel>
                    <Input
                      {...field}
                      id="fullName"
                      aria-invalid={fieldState.invalid}
                      placeholder="Nhập họ và tên"
                      autoComplete="name"
                    />
                    {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                  </Field>
                )}
              />

              {/* Email & username chỉ đọc — không có trong payload cập nhật */}
              <Field>
                <FieldLabel htmlFor="email" className="cursor-pointer">
                  <Mail className="h-4 w-4" /> Email đăng nhập
                </FieldLabel>
                <Input
                  id="email"
                  type="email"
                  value={user?.email ?? ''}
                  readOnly
                  disabled
                  className="pointer-events-none"
                />
              </Field>

              <Field>
                <FieldLabel htmlFor="username" className="cursor-pointer">
                  <UserIcon className="h-4 w-4" /> Tên đăng nhập
                </FieldLabel>
                <Input
                  id="username"
                  value={user?.username ?? ''}
                  readOnly
                  disabled
                  className="pointer-events-none"
                />
              </Field>

              <Controller
                name="avatarUrl"
                control={control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid} className="sm:col-span-2">
                    <FieldLabel htmlFor="avatarUrl" className="cursor-pointer">
                      URL ảnh đại diện
                    </FieldLabel>
                    <Input
                      {...field}
                      id="avatarUrl"
                      value={field.value ?? ''}
                      aria-invalid={fieldState.invalid}
                      placeholder="https://…"
                    />
                    {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                  </Field>
                )}
              />
            </FieldGroup>
          </form>
          <Button
            type="submit"
            form="update-profile-form"
            variant="default"
            className="mt-4 w-full"
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? (
              <Loader2 className="animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            {isSubmitting ? 'Đang cập nhật...' : 'Cập nhật thông tin'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
