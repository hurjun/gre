import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// During development, /api is proxied to the FastAPI server so the frontend
// and backend can run on separate ports without CORS friction.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
