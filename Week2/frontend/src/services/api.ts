/** API 客户端基础配置 */
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 秒
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 错误处理
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // 统一错误处理
    if (error.response) {
      // 服务器返回了错误状态码
      const errorData = error.response.data as { code?: string; message?: string; details?: unknown };
      const errorMessage = errorData?.message || error.message || '请求失败';
      console.error('API Error:', errorMessage, errorData);
      return Promise.reject(new Error(errorMessage));
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('Network Error:', error.message);
      return Promise.reject(new Error('网络错误，请检查连接'));
    } else {
      // 其他错误
      console.error('Error:', error.message);
      return Promise.reject(error);
    }
  }
);

export default apiClient;
