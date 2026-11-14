import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// Dev proxy adds X-API-Key server-side (production: api/proxy.js).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const target = env.API_URL ?? 'http://localhost:8000';
  return {
    plugins: [react()],
    server: {
      port: 5174,
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
          headers: { 'X-API-Key': env.API_KEY ?? '' },
        },
      },
    },
  };
});
