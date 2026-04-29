import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Proxy all /api requests to the FastAPI backend.
      // This eliminates cross-origin issues with HTTP-only cookies in development:
      // the browser sees all requests as coming from localhost:5173, so cookies set
      // by the backend (on localhost) are forwarded correctly via withCredentials.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
