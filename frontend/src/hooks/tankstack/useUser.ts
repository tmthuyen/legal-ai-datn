import { userApi } from '@/apis/user.api';
import { parseAxiosError } from '@/lib/axiosClient';
import { ApiResponse, UpdateProfileDto, User } from '@/shared/types/api.types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import React from 'react';
import { toast } from 'sonner';

// get all
export function useGetAll(
  staleTime: number = 1000 * 60 * 5,
  gcTime: number = 1000 * 60 * 10,
  page: number = 1,
  limit: number = 10,
) {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await userApi.getAllUsers({ page, limit });
      return response.result;
    },
    staleTime: staleTime, // 5 minutes
    gcTime: gcTime, // 10 minutes,
  });
}

// get one
export function useGetOne(
  id: number,
  staleTime: number = 1000 * 60 * 2,
  gcTime: number = 1000 * 60 * 5,
) {
  return useQuery({
    queryKey: ['users', id],
    queryFn: async () => {
      const response = await userApi.getUserById(id);
      return response.result;
    },
    staleTime: staleTime,
    gcTime: gcTime,
  });
}

// create
export function useCreate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { name: string }) => {
      const response = await userApi.createUser(data);
      return response;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success(data.message || 'Tạo người dùng thành công!');
    },
    onError: (error: any) => {
      const parsedError = parseAxiosError(error);
      toast.error(`Lỗi: ${parsedError.message || 'Vui lòng thử lại.'}`);
    },
  });
}

// update
const useUpdate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: any }) => {
      const response = await userApi.updateUserAdmin(id, data);
      return response;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success(data.message || 'Cập nhật thông tin người dùng thành công!');
    },
    onError: (error: any) => {
      const parsedError = parseAxiosError(error);
      toast.error(`Lỗi: ${parsedError.message || 'Vui lòng thử lại.'}`);
    },
  });
};

// delete
const useDelete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await userApi.deleteUser(id);
      return response;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success(data.message || 'Xóa người dùng thành công!');
    },
    onError: (error: any) => {
      const parsedError = parseAxiosError(error);
      toast.error(`Lỗi: ${parsedError.message || 'Vui lòng thử lại.'}`);
    },
  });
};

// update me
const useUpdateMe = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UpdateProfileDto) => {
      const response = await userApi.updateProfile(data);
      return response;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success(data.message || 'Cập nhật thông tin người dùng thành công!');
    },
    onError: (error: any) => {
      const parsedError = parseAxiosError(error);
      toast.error(`Lỗi: ${parsedError.message || 'Vui lòng thử lại.'}`);
    },
  });
};

// avatar
const useUpdateAvatar = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await userApi.updateUserAvatar(formData);
      return response;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success(data.message || 'Cập nhật avatar thành công!');
    },
    onError: (error: any) => {
      const parsedError = parseAxiosError(error);
      toast.error(`Lỗi: ${parsedError.message || 'Vui lòng thử lại.'}`);
    },
  });
};

const useUser = {
  useGetAll,
  useGetOne,
  useCreate,
  useUpdate,
  useDelete,
  useUpdateMe,
  useUpdateAvatar,
};

export default useUser;
