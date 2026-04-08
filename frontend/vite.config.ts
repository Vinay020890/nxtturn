// C:\Users\Vinay\Project\frontend\vite.config.ts

import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig(({ command, mode }) => {
  // Load environment variables if needed
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      vue(),
      vueDevTools(),
      // This plugin automatically turns on HTTPS for the dev server
      command === 'serve' ? basicSsl() : [],
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: true,
      port: 5173,
      allowedHosts: true,
      // Removed the 'https' line to fix the TypeScript error.
      // The basicSsl() plugin above will handle the SSL setup for us.
    },
  }
})
