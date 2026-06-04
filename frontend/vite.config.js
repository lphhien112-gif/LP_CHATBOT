import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev: Vite (5173) phục vụ ở "/" (mở http://localhost:5173 là chạy) và proxy các
//      lời gọi API sang FastAPI backend (8000).
// Prod: `npm run build` dùng base "/app/" và xuất ra ../static/app để FastAPI phục vụ.
const BACKEND = 'http://localhost:8000'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === 'build' ? '/app/' : '/',
  server: {
    port: 5173,
    host: true, // cho phép truy cập qua localhost, 127.0.0.1 và IP mạng LAN
    proxy: {
      '/send_message': { target: BACKEND, changeOrigin: true },
      '/reset_chat_session': { target: BACKEND, changeOrigin: true },
      '/api': { target: BACKEND, changeOrigin: true },
    },
  },
  build: {
    outDir: '../static/app',
    emptyOutDir: true,
  },
}))
