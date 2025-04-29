import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: resolve(__dirname, '../frontend/static/www/html'), // THIS
    emptyOutDir: true,
  },
  base: './', // important: relative paths
})