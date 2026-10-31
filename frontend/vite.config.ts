import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '127.0.0.1',
    port: Number(process.env.LIFESIM_WEB_PORT || 5173),
    strictPort: true,
    proxy: { '/api': { target: process.env.LIFESIM_PROXY_TARGET || `http://127.0.0.1:${process.env.LIFESIM_API_PORT || 8000}` } },
  },
  build: { chunkSizeWarningLimit: 700 },
});
