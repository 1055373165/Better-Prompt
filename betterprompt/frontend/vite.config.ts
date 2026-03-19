import { defineConfig, loadEnv, type UserConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

type BetterPromptViteConfig = UserConfig & {
  test?: {
    environment: string;
    setupFiles: string;
  };
};

export default defineConfig(({ mode }): BetterPromptViteConfig => {
  const env = loadEnv(mode, process.cwd(), '');
  const frontendPort = Number(env.BETTERPROMPT_FRONTEND_PORT || 5173);
  const backendPort = Number(env.BETTERPROMPT_BACKEND_PORT || 8000);

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: frontendPort,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: `http://127.0.0.1:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
    },
  };
});
