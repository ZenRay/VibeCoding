/** API 客户端基础配置 */
import axios, { AxiosInstance, AxiosError } from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
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
  },
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
      const errorData = error.response.data as any;

      console.log("API Error - 原始响应数据:", errorData);

      let errorMessage = "请求失败";

      // 处理 FastAPI 的错误格式
      if (errorData?.detail) {
        if (typeof errorData.detail === "string") {
          // detail 是字符串
          errorMessage = errorData.detail;
        } else if (typeof errorData.detail === "object") {
          // detail 是对象（例如 {code: "...", message: "..."}）
          if (errorData.detail.message) {
            errorMessage = errorData.detail.message;
          } else {
            // 将整个对象序列化为字符串
            errorMessage = JSON.stringify(errorData.detail);
          }
        }
      } else if (errorData?.message) {
        errorMessage = errorData.message;
      } else if (error.message) {
        errorMessage = error.message;
      }

      console.error("API Error:", {
        status: error.response.status,
        url: error.config?.url,
        message: errorMessage,
        rawData: errorData,
      });

      // 创建增强的错误对象，保留原始响应信息
      const enhancedError = new Error(errorMessage) as Error & {
        response?: typeof error.response;
        status?: number;
      };
      enhancedError.response = error.response;
      enhancedError.status = error.response.status;

      return Promise.reject(enhancedError);
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error("Network Error:", error.message);
      return Promise.reject(new Error("网络错误，请检查连接"));
    } else {
      // 其他错误
      console.error("Error:", error.message);
      return Promise.reject(error);
    }
  },
);

export default apiClient;
