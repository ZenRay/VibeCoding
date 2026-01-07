import axios, { AxiosError, AxiosInstance } from 'axios'
import { ApiError } from '@/types/api'

// 在浏览器环境中，使用相对路径通过 Vite 代理访问后端
// 在 Docker 环境中，Vite 代理会将请求转发到 backend 服务
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证 token 等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError<ApiError>) => {
    // 统一错误处理
    if (error.response) {
      // 服务器返回了错误响应
      const apiError = error.response.data
      console.error('API Error:', apiError)
      return Promise.reject(apiError)
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('Network Error:', error.message)
      return Promise.reject({
        error: {
          code: 'NETWORK_ERROR',
          message: '网络错误，请检查网络连接',
        },
      })
    } else {
      // 其他错误
      console.error('Error:', error.message)
      return Promise.reject({
        error: {
          code: 'UNKNOWN_ERROR',
          message: error.message || '未知错误',
        },
      })
    }
  }
)

export default api
