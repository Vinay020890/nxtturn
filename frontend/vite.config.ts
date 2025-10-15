import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite' // <-- Import loadEnv
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // <-- Change to a function to access 'mode'
  // Load env file based on the current mode (e.g., 'development', 'cy.network')
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue(), vueDevTools()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    // --- ADD THIS ENTIRE 'server' BLOCK ---
    server: {
      host: '0.0.0.0', // Listen on all network interfaces
      port: 5173, // Default port for development
      hmr: {
        // This explicitly tells the HMR client how to connect.
        // We will use an environment variable for the host to stay flexible.
        clientPort: 5173,
        host: env.VITE_WEBSOCKET_HOST || 'localhost',
        protocol: 'ws',
      },
    },
  }
})
