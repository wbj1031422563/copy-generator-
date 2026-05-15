import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
  },
  server: {
    host: true,
    port: Number(process.env.VITE_PORT || process.env.PORT || 5173),
    strictPort: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY || 'http://127.0.0.1:8765',
        changeOrigin: true,
      },
    },
  },
})
