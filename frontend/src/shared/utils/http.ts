import { ApiErrorBody, ApiOkBody } from '../types/api.types';

export interface ApiResponse<T> {
  success: boolean;
  status: number;
  message: string;
  data?: T;
  details?: string[];
}

export interface FetchOptions extends Omit<RequestInit, 'method' | 'body'> {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: any; // This will be JSON.stringified in the fetcher
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:3002/api';
console.log('API_BASE_URL:', API_BASE_URL);

const BASE_HEADERS = {
  'Content-Type': 'application/json',
  // Add any other default headers here, e.g., Authorization if needed
};

const fetcher = async <T>(url: string, options?: FetchOptions): Promise<ApiResponse<T>> => {
  const fetchOptions = {
    method: options?.method || 'GET',
    headers: {
      ...BASE_HEADERS,
      ...options?.headers,
    },
    body: options?.body ? JSON.stringify(options.body) : undefined,
    ...(options &&
      Object.fromEntries(
        Object.entries(options).filter(([key]) => !['method', 'headers', 'body'].includes(key)),
      )),
  };

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, fetchOptions);

    const responseData: ApiOkBody<T> | ApiErrorBody = await response.json();

    if (!response.ok) {
      return {
        success: false,
        status: response.status,
        message: responseData.message || 'An error occurred',
        details: 'details' in responseData ? responseData.details : undefined,
      };
    }

    const apiResponse: ApiResponse<T> = {
      success: true,
      status: response.status,
      message: responseData.message || 'Request successful',
      data: 'data' in responseData ? responseData.data : undefined,
    };
    return apiResponse;
  } catch (error) {
    console.error('Fetch error:', error);
    return {
      success: false,
      status: 500,
      message: error instanceof Error ? error.message : 'An unexpected error occurred',
      data: undefined,
      // details: error instanceof Error ? [error.stack || 'No stack trace available'] : undefined,
    };
  }
};

// get
export const getUtil = async <T>(url: string, options?: FetchOptions): Promise<ApiResponse<T>> => {
  return fetcher<T>(url, { ...options, method: 'GET' });
};

// post
export const postUtil = async <T>(url: string, options?: FetchOptions): Promise<ApiResponse<T>> => {
  console.log('postUtil called with url:', url, 'options:', options);
  return fetcher<T>(url, { ...options, method: 'POST' });
};

// put
export const putUtil = async <T>(url: string, options?: FetchOptions): Promise<ApiResponse<T>> => {
  return fetcher<T>(url, { ...options, method: 'PUT' });
};

// delete
export const delUtil = async <T>(url: string, options?: FetchOptions): Promise<ApiResponse<T>> => {
  return fetcher<T>(url, { ...options, method: 'DELETE' });
};
