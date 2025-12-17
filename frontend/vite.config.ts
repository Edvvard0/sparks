import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { nodePolyfills } from 'vite-plugin-node-polyfills'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    nodePolyfills({
      // Включаем полифиллы для Buffer и других Node.js API
      globals: {
        Buffer: true,
        global: true,
        process: true,
      },
    }),
  ],
  server: {
    host: true,
    allowedHosts: [
      'bursting-smart-eagle.ngrok-free.app',
      'rightfully-integral-whitebait.cloudpub.ru',
      '.cloudpub.ru',
      'localhost',
      '.ngrok-free.app',
      '.ngrok.io',
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => {
          // Проксируем /api/v1/* на http://localhost:8000/api/v1/*
          // Vite автоматически добавит /api/v1 к пути
          return path;
        },
      },
    },
  },
  publicDir: 'public',
})
