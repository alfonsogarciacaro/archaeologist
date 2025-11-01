import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: parseInt(process.env.UI_DEV_PORT ?? ''),
    proxy: {
      '/api': {
        target: `http://localhost:${process.env.WEB_PORT}`,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'build',
  },
})