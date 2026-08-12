import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// GH_PAGES=1 is set only by the Pages deploy workflow, so local/Docker
// builds keep serving from "/".
export default defineConfig({
  base: process.env.GH_PAGES ? '/magnet/' : '/',
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
