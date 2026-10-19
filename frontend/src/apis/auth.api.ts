import { ApiResponse, RegisterData, UpdatePasswordData, User } from '@/shared/types/api.types';
import axiosClient from '../lib/axiosClient';

export const authApi = {
  login: async ({
    username,
    password,
  }: {
    username: string;
    password: string;
  }): Promise<ApiResponse<{ accessToken: string; refreshToken: string }>> => {
    const { data } = await axiosClient.post('/auth/login', { username, password });

    return data;
  },

  register: async (
    registerData: RegisterData,
  ): Promise<ApiResponse<{ accessToken: string; refreshToken: string }>> => {
    const { data } = await axiosClient.post('/auth/register', registerData);

    return data;
  },

  loginGoogle: async (data: {
    idToken?: string;
    code?: string;
    redirectUri?: string;
  }): Promise<ApiResponse<{ accessToken: string; refreshToken: string }>> => {
    const response = await axiosClient.post('/auth/login-google', data);

    return response.data;
  },

  refresh: async (): Promise<ApiResponse<{ accessToken: string; refreshToken: string }>> => {
    const { data } = await axiosClient.post('/auth/refresh', null, { withCredentials: true });

    return data;
  },

  getMe: async (): Promise<ApiResponse<User>> => {
    const { data } = await axiosClient.get('/auth/me');

    return data;
  },

  sendVerificationEmail: async (): Promise<ApiResponse<any>> => {
    const { data } = await axiosClient.post('/auth/send-verification-email');

    return data;
  },
  verifyEmail: async (token: string): Promise<ApiResponse<any>> => {
    const { data } = await axiosClient.post(`/auth/verify-email`, { token });

    return data;
  },

  getSessions: async (): Promise<ApiResponse<any[]>> => {
    const { data } = await axiosClient.get('/auth/sessions');

    return data;
  },

  logout: async (): Promise<void> => {
    return axiosClient.post('/auth/logout');
  },

  logoutBySession: async (data: { sessionId: string }): Promise<void> => {
    return axiosClient.post(`/auth/logout-session/${data.sessionId}`);
  },

  logoutAll: async (): Promise<void> => {
    return axiosClient.post('/auth/logout-all');
  },

  updatePassword: async (updatePasswordData: UpdatePasswordData): Promise<ApiResponse<any>> => {
    const { data } = await axiosClient.patch('/auth/change-password', updatePasswordData);
    return data;
  },
};
