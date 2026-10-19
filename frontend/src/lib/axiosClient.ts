import axios from 'axios';
import { keysToCamel } from '@/shared/utils/snakeToCamel';
import { useAuthStore } from '@/stores/auth.store';
import { ApiErrorResponse } from '@/shared/types/api.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

const axiosClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

export const parseAxiosError = (
  error: any,
  customMessage?: string,
): { statusCode: number; message: string } => {
  let statusCode = 500;
  if (axios.isAxiosError(error)) {
    console.error('[Axios] Error response:', error.response);
    const serverResponse: ApiErrorResponse = error.response?.data;

    statusCode = error.response?.status || serverResponse?.statusCode || 500;
    if (statusCode >= 500) {
      return {
        statusCode,
        message: 'Lỗi máy chủ, vui lòng thử lại sau.',
      };
    }
    if (serverResponse && serverResponse.message) {
      return {
        statusCode: error.response?.status || serverResponse.statusCode || 500,
        message: customMessage || serverResponse.message || 'Có lỗi xảy ra',
      };
    }
    return {
      statusCode: error.response?.status || serverResponse?.statusCode || 500,
      message: customMessage || 'Có lỗi xảy ra',
    };
  }
  return {
    statusCode,
    message: customMessage || 'Có lỗi xảy ra',
  };
};

const setAuthTokenInContext: ((token: string | null) => void) | null = null;
const currentAccessToken: string | null = null;

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (token) prom.resolve(token);
    else prom.reject(error);
  });
  failedQueue = [];
};

// export const injectAuthFunctions = (setTokenFn: (token: string | null) => void) => {
//   setAuthTokenInContext = setTokenFn;
// };

// export const updateToken = (token: string | null) => {
//   currentAccessToken = token;
//   if (setAuthTokenInContext) {
//     setAuthTokenInContext(token);
//   }
// };

// export const getCurrentToken = () => {
//   return currentAccessToken;
// };

// Request Interceptor
axiosClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('[Axios] Request error:', error);
    return Promise.reject(error);
  },
);

// Response Interceptor
axiosClient.interceptors.response.use(
  (response) => {
    if (response.data) {
      // console.log(response.data);
      response.data = keysToCamel(response.data);
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    if (originalRequest.url.includes('/auth/refresh')) {
      useAuthStore.getState().setAccessToken(null);
      processQueue(error, null);
      console.log('Failed to refresh token');
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers['Authorization'] = `Bearer ${token}`;
            return axiosClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axiosClient.post(`/auth/refresh`, null, { withCredentials: true });

        // console.log('Refresh Response: ', response.data);
        const { accessToken: newAccessToken } = response?.data?.result;
        // console.log("newAccessToken", newAccessToken)

        useAuthStore.getState().setAccessToken(newAccessToken);

        processQueue(null, newAccessToken);

        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
        return axiosClient(originalRequest);
      } catch (refreshError) {
        console.log('Refresh Error: ', refreshError);
        useAuthStore.getState().setAccessToken(null);
        processQueue(refreshError, null);
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  },
);

export default axiosClient;
