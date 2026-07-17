import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 개발 서버: /api 요청을 백엔드(FastAPI)로 프록시
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
