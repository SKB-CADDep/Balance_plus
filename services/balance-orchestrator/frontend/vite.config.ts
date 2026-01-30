import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      // 1. Запросы к нашему Оркестратору (локально)
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      // 2. Запросы к удаленному калькулятору штоков
      '/wsa-api': {
        target: 'http://10.202.220.143:5253', // <-- Ваш удаленный сервер
        changeOrigin: true,
        secure: false,
        // Переписываем путь: /wsa-api/turbines -> /api/v1/turbines
        rewrite: (path) => path.replace(/^\/wsa-api/, '/api/v1') 
      }
    }
  }
})