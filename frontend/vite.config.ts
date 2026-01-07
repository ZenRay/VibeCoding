import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(() => {
  // 在 Docker 环境中，使用 backend 服务名（同一网络）
  // 本地开发时使用 localhost
  const isDocker = process.env.VITE_DOCKER === 'true'
  const apiTarget = isDocker ? 'http://backend:8000' : 'http://localhost:8000'

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      host: true,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
          ws: true, // 支持 WebSocket
        },
      },
    },
  }
})
