import { legalUserApi } from '@/apis/legal.api';
import { parseAxiosError } from '@/lib/axiosClient';
import {
  UpdatePasswordPayload,
  UpdateProfilePayload,
  LegalUser,
} from '@/shared/types/legal.types';
import { useAuthStore } from '@/stores/auth.store';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';

/** Cập nhật hồ sơ (`PUT /user/profile`) → đồng bộ lại `user` trong `useAuthStore`. */
export function useUpdateProfile() {
  return useMutation({
    mutationFn: (payload: UpdateProfilePayload) => legalUserApi.updateProfile(payload),
    onSuccess: (response) => {
      if (response.result) {
        useAuthStore.getState().setUser(response.result as LegalUser);
      }
      toast.success(response.message || 'Cập nhật hồ sơ thành công.');
    },
    onError: (error) =>
      toast.error(parseAxiosError(error).message || 'Không thể cập nhật hồ sơ. Vui lòng thử lại.'),
  });
}

/** Đổi mật khẩu (`PUT /user/password`). */
export function useUpdatePassword() {
  return useMutation({
    mutationFn: (payload: UpdatePasswordPayload) => legalUserApi.updatePassword(payload),
    onSuccess: (response) => {
      toast.success(response.message || 'Đổi mật khẩu thành công.');
    },
    onError: (error) =>
      toast.error(parseAxiosError(error).message || 'Không thể đổi mật khẩu. Vui lòng thử lại.'),
  });
}
