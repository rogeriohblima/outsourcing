import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// vite.config.ts
// Quando VITE_API_URL for vazio (build Docker), o cliente HTTP usa
// caminhos relativos (/api/v1/...) — o Nginx faz o proxy para o backend.
// Em desenvolvimento local (npm run dev), usa http://localhost:8000.

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})