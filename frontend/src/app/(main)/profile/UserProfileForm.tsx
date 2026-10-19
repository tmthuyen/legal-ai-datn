'use client';

import React, { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  User as UserIcon,
  Mail,
  Camera,
  Loader2,
  EyeOffIcon,
  EyeIcon,
  PhoneCall,
  Save,
  Shield,
  UserCheck,
} from 'lucide-react';

import { Calendar as CalendarIcon } from 'lucide-react';
import { userApi } from '@/apis/user.api';
import { useAuthStore } from '@/stores/auth.store';
import { Genre, Role, UpdateProfileDto, User } from '@/shared/types/api.types';
import { mapUserStatus } from '@/shared/utils/mapStatus';
import { usePathname, useRouter } from 'next/navigation';
import {
  Field,
  FieldContent,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from '@/components/ui/field';
import { Controller, ControllerFieldState, ControllerRenderProps, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import z from 'zod';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const updateProfileSchema = z.object({
  fullName: z
    .string()
    .min(5, 'Tên hiển thị không được quá ngắn hơn 5 ký tự')
    .max(50, 'Tên hiển thị không được quá dài hơn 50 ký tự'),
  email: z.email('Email không hợp lệ').optional(),
  gender: z.string().optional(),
  birthDate: z
    .string()
    .optional()
    .refine((value) => {
      if (!value) return true; // Allow empty value
      const date = new Date(value);
      // kiem tra nho hon 5 tuoi
      return date <= new Date(new Date().setFullYear(new Date().getFullYear() - 5));
    }, 'Ngày sinh không hợp lệ. Bạn phải ít nhất 5 tuổi.'),
  phoneNumber: z
    .string()
    .optional()
    .refine((value) => {
      if (!value) return true; // Allow empty value
      const phoneRegex = /^(0|\+84)(\d{9,10})$/;
      return phoneRegex.test(value);
    }, 'Số điện thoại không hợp lệ'),
  avatarUrl: z.string().optional(),
  preferenceData: z.array(z.string()).optional(),
  address: z.string().optional(),
});

const genderOptions = [
  { value: 'MALE', label: 'Nam' },
  { value: 'FEMALE', label: 'Nữ' },
  { value: 'OTHER', label: 'Khác' },
];

import {
  InputMultiSelect,
  InputMultiSelectTrigger,
} from '@/components/extend-ui/input-multiselect';
import { useQuery } from '@tanstack/react-query';
import { genreApi } from '@/apis/genre.api';
import { parseAxiosError } from '@/lib/axiosClient';
import Spining from '@/components/loading/spining';
import useGenre from '@/hooks/tankstack/useGenre';
import useUser from '@/hooks/tankstack/useUser';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { format } from 'date-fns';
import { Calendar } from '@/components/ui/calendar';
import dateTimeUtils from '@/shared/utils/formatting';
import { Separator } from '@/components/ui/separator';
import { authApi } from '@/apis/auth.api';
import useAuthApi from '@/hooks/tankstack/useAuthApi';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface InputMultiSelectDemoProps {
  field: ControllerRenderProps<
    {
      fullName: string;
      email?: string | undefined;
      gender?: string | undefined;
      birthDate?: string | undefined;
      phoneNumber?: string;
      avatarUrl?: string | undefined;
      preferenceData?: string[] | undefined;
      address?: string | undefined;
    },
    'preferenceData'
  >;
  fieldState: ControllerFieldState;
  genres: Genre[];
}

// const genreOptions: Genre[] = [
//   { id: '1', name: 'Hành động' },
//   { id: '2', name: 'Kinh dị' },
//   { id: '3', name: 'Tình cảm' },
//   { id: '4', name: 'Hài hước' },
//   { id: '5', name: 'Khoa học viễn tưởng' },
// ];
const displayText = {
  placeholder: 'Chọn...',
  selectAll: 'Chọn tất cả',
  clear: 'Xóa',
  close: 'Đóng',
  search: 'Tìm kiếm',
};
export const InputMultiSelectDemo = ({ field, fieldState, genres }: InputMultiSelectDemoProps) => {
  const selectIds = genres
    .filter((genre) => {
      if (!field.value || field.value.length === 0) return false;
      return field.value.some((selectedGenre) => selectedGenre === genre.name);
    })
    .map((genre) => genre.id);
  const genreOptions = genres.map((genre) => ({
    value: genre.id,
    label: genre.name,
  }));

  const mapValueToName = (selectedValues: string[] | undefined) => {
    if (!selectedValues || selectedValues.length === 0) return [];
    return selectedValues.map((value) => {
      const genre: Genre | undefined = genres.find((g) => g.id === value);
      return genre ? genre.name : '';
    });
  };

  return (
    <div className="space-y-6">
      {/* <Input
        value={field.value?.join(', ')} // Display the selected genre names
        id="preferenceData"
        readOnly
        aria-invalid={fieldState.invalid}
        placeholder="Thể loại yêu thích"
      /> */}

      {/* display genre names */}
      <div className="flex flex-wrap gap-2">
        {field.value &&
          field.value.map((name, index) => (
            <span
              key={index}
              className="border-primary text-primary bg-primary/20 rounded-md border px-2 py-1 text-sm"
            >
              {name}
            </span>
          ))}
        {field.value && field.value.length === 0 && (
          <span className="text-sm text-gray-400">Chưa chọn thể loại yêu thích</span>
        )}
      </div>

      <InputMultiSelect
        options={genreOptions}
        value={selectIds}
        onValueChange={(newValues) => {
          field.onChange(mapValueToName(newValues)); // Update the form state with the selected genres
          // console.log('Selected genre IDs:', field.value);
        }}
        displayTextProps={displayText}
      >
        {(provided) => <InputMultiSelectTrigger {...provided} />}
      </InputMultiSelect>
    </div>
  );
};

export default function UserProfileForm() {
  const user = useAuthStore((state) => state.user);
  const router = useRouter();
  const pathname = usePathname();

  // mutation & query
  const { data: genres, isLoading: isGenresLoading, error: genresError } = useGenre.useGetAll();
  const sendVerificationEmailMutation = useAuthApi.useSendVerificationEmail();
  const updateMeMutation = useUser.useUpdateMe();
  const updateAvatarMutation = useUser.useUpdateAvatar();

  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Vui lòng chọn file hình ảnh');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('Kích thước ảnh tối đa 5MB');
      return;
    }

    // check file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Chỉ cho phép định dạng ảnh (jpg, png, gif)');
      return;
    }

    setIsUploadingAvatar(true);
    const formData = new FormData();
    formData.append('file', file);

    return await updateAvatarMutation.mutateAsync(formData, {
      onSuccess: (data) => {
        useAuthStore.getState().refreshUser();
      },
    });
  };

  const status = mapUserStatus(user?.status || 'INACTIVE');

  const [error, setError] = useState<string | null>(null);
  const updateProfileForm = useForm<z.infer<typeof updateProfileSchema>>({
    resolver: zodResolver(updateProfileSchema),
    mode: 'onChange',
    defaultValues: {
      fullName: user?.fullName || '',
      email: user?.email || undefined,
      gender: user?.gender,
      birthDate: user?.birthDate ? new Date(user.birthDate).toISOString().split('T')[0] : undefined,
      preferenceData: user?.preferenceData ? user?.preferenceData?.genre : [],
      address: user?.address || undefined,
      avatarUrl: user?.avatarUrl || undefined,
      phoneNumber: user?.phoneNumber || '',
    },
  });

  const {
    control,
    reset,
    handleSubmit,
    formState: { isValid, isSubmitting },
  } = updateProfileForm;

  const onSubmit = async (data: z.infer<typeof updateProfileSchema>) => {
    setError(null);

    const preferenceData = data.preferenceData ? { genre: data.preferenceData } : undefined;

    const payload: UpdateProfileDto = {
      fullName: data.fullName,
      gender: data.gender,
      birthDate: data.birthDate ? new Date(data.birthDate) : undefined,
      phoneNumber: data.phoneNumber || '',
      avatarUrl: data.avatarUrl || '',
      preferenceData,
    };
    console.log('Update profile data:', payload);

    return await updateMeMutation.mutateAsync(payload, {
      onSuccess: (data) => {
        // toast.success(data.message || 'Cập nhật thông tin người dùng thành công!');
        useAuthStore.getState().refreshUser();
      },
    });

    // refresh user data in auth store
  };

  // fetch genres from API, tankstack query
  if (genresError) {
    const parsedError = parseAxiosError(genresError);
    toast.error(`Lỗi khi tải danh sách thể loại: ${parsedError.message || 'Vui lòng thử lại.'}`);
  }

  // check loading
  if (isGenresLoading) {
    return <Spining isLocalLoading={true} />;
  }

  // check xác thực bơi email, gg, fb, apple
  const verifiedBy = (user: User | null) => {
    if (!user || !user.isVerified) return '';
    const providerText = 'Xác thực bằng: ';

    const provider = 'email';
    return providerText + provider;
  };

  const handleSendVerificationEmail = async () => {
    await sendVerificationEmailMutation.mutateAsync();
  };

  return (
    <Card className="w-full overflow-hidden border-gray-200 bg-white shadow-lg dark:border-slate-800 dark:bg-slate-900">
      <CardHeader>
        <div className="flex flex-col items-center justify-center gap-2">
          <FieldLabel className="me-auto cursor-pointer text-lg" htmlFor="avatarInput">
            Ảnh đại diện
          </FieldLabel>
          <div className="relative mx-auto">
            {/* Avatar */}
            <Avatar className="h-24 w-24">
              <AvatarImage
                src={user?.avatarUrl || 'https://github.com/shadcn.png'}
                alt={user?.fullName || '@shadcn'}
              />
              <AvatarFallback>{user?.fullName?.charAt(0) || 'U'}</AvatarFallback>
            </Avatar>
            <Button
              size="icon"
              className="absolute right-0 bottom-0 rounded-full hover:scale-110"
              onClick={handleAvatarClick}
            >
              {!updateAvatarMutation.isPending ? (
                <Camera className="" />
              ) : (
                <Loader2 className="animate-spin" />
              )}
            </Button>
          </div>

          <FieldDescription>JPG, PNG hoặc GIF. Tối đa 5MB.</FieldDescription>
          <FieldDescription>Nhấp vào icon camera để chọn ảnh.</FieldDescription>
          <input
            id="avatarInput"
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            className="hidden"
          />
        </div>
        <Separator className="my-2" />
      </CardHeader>
      <CardContent className="pt-0">
        <div className="mb-4 flex flex-col gap-2">
          <Field>
            <FieldLabel className="cursor-pointer">
              <UserCheck className="h-4 w-4" /> Trạng thái tài khoản
            </FieldLabel>
            <FieldContent className="flex flex-row flex-wrap items-center justify-between gap-2">
              <span className={`rounded-md p-2 text-xs font-semibold ${status.color}`}>
                {status.label}
              </span>

              {/* check is verified */}
              {user?.isVerified && (
                <span
                  className={`rounded-md bg-green-100 p-2 text-xs font-semibold text-green-800 dark:bg-green-800/60 dark:text-green-400`}
                >
                  Đã xác thực
                </span>
              )}

              {/* check is verified */}
              {!user?.isVerified && (
                <Button className="" onClick={handleSendVerificationEmail}>
                  {!sendVerificationEmailMutation.isPending ? (
                    <Mail className="h-4 w-4" />
                  ) : (
                    <Loader2 className="animate-spin" />
                  )}{' '}
                  Xác thực tài khoản
                </Button>
              )}
            </FieldContent>
          </Field>
          <Field>
            <FieldLabel className="cursor-pointer">
              <Shield className="h-4 w-4" /> Vai trò
            </FieldLabel>
            <FieldContent className="flex flex-row flex-wrap gap-2">
              {user?.roles.map((role: Role) => (
                <Badge
                  key={role.code}
                  variant={role.code === 'ADMIN' ? 'destructive' : 'default'}
                  className="text-sm uppercase"
                >
                  {role.code}
                </Badge>
              ))}
            </FieldContent>
          </Field>
        </div>

        <Separator className="my-4" />

        <div className="flex flex-col gap-4">
          <form id="update-profile-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* API err message */}
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
                      autoComplete="fullName"
                    />
                    {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                  </Field>
                )}
              />
              {/* email */}
              <Controller
                name="email"
                control={control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="email" className="cursor-pointer">
                      <Mail className="h-4 w-4" /> Email đăng nhập
                    </FieldLabel>
                    <Input
                      {...field}
                      id="email"
                      type="email"
                      aria-invalid={fieldState.invalid}
                      placeholder="Nhập email"
                      autoComplete="email"
                      className="pointer-events-none"
                      disabled
                    />
                    {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                  </Field>
                )}
              />

              {/* gender selection */}
              <Controller
                name="gender"
                control={control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="gender" className="cursor-pointer">
                      Giới tính
                    </FieldLabel>
                    <Select name={field.name} value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          <SelectLabel>Giới tính</SelectLabel>
                          {genderOptions.map((item) => (
                            <SelectItem key={item.value} value={item.value}>
                              {item.label}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                    {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                  </Field>
                )}
              />

              {/* birthday */}
              <Controller
                name="birthDate"
                control={control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="birthDate" className="cursor-pointer">
                      <CalendarIcon className="h-4 w-4" />{' '}
                      {/* Đổi tên để tránh trùng với component Calendar bên dưới */}
                      Ngày sinh
                    </FieldLabel>

                    <Popover>
                      <PopoverTrigger asChild>
                        {/* Dùng asChild nếu Button của bạn tự render thẻ button, tránh lỗi lồng thẻ button */}
                        <Button
                          id="birthDate"
                          variant="outline"
                          data-empty={!field.value}
                          className="data-[empty=true]:text-muted-foreground w-full justify-start text-left font-normal"
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {field.value ? (
                            dateTimeUtils.formatShortDate(field.value)
                          ) : (
                            <span>Chọn ngày sinh</span>
                          )}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          defaultMonth={field.value ? new Date(field.value) : undefined}
                          captionLayout="dropdown"

                          selected={field.value ? new Date(field.value) : undefined}
                          onSelect={(date) => {
                            if (date) {
                              field.onChange(format(date, 'yyyy-MM-dd')); // Chuyển đổi thành định dạng YYYY-MM-DD
                            }
                          }}
                          disabled={
                            (date: Date) => date > new Date() || date < new Date('1900-01-01') // Giới hạn ngày sinh hợp lý
                          }
                        />
                      </PopoverContent>
                    </Popover>

                    {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                  </Field>
                )}
              />

              {/* phone */}
              <Controller
                name="phoneNumber"
                control={control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="phoneNumber" className="cursor-pointer">
                      <PhoneCall className="h-4 w-4" />
                      Số điện thoại
                    </FieldLabel>
                    <Input
                      {...field}
                      id="phoneNumber"
                      type="tel"
                      aria-invalid={fieldState.invalid}
                      placeholder="Nhập số điện thoại"
                      autoComplete="tel"
                    />
                    {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                  </Field>
                )}
              />

              {/* preferences data */}
              {/* load genres */}
              {/* multi select genres */}
              <div className="col-span-full">
                <Controller
                  name="preferenceData"
                  control={control}
                  render={({ field, fieldState }) => (
                    <Field data-invalid={fieldState.invalid}>
                      <FieldLabel htmlFor="preferenceData" className="cursor-pointer">
                        Thể loại yêu thích
                      </FieldLabel>
                      <InputMultiSelectDemo
                        field={field}
                        fieldState={fieldState}
                        genres={genres || []}
                      />
                      {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                    </Field>
                  )}
                />
              </div>
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
