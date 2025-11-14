import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// IMPORTANT: set base to your repo name when deploying to GitHub Pages
// e.g., base: '/my-blog/'
export default defineConfig({
  plugins: [react()],
  base: '/my-tech-blog/'
})