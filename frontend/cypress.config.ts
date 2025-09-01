import { defineConfig } from "cypress";
import dotenv from "dotenv";

// This logic reads the ENV_FILE variable we will set in our npm script.
// It defaults to the local file if no variable is set.
const envFile = process.env.ENV_FILE || '.env.cy.local';
dotenv.config({ path: envFile });

export default defineConfig({
  e2e: {
    // The baseUrl is now dynamically loaded from our .env files
    baseUrl: process.env.CYPRESS_BASE_URL,
    
    setupNodeEvents(on, config) {
      // You can pass all environment variables to the browser tests
      // This is useful if you ever need them in your test scripts
      config.env = {
        ...config.env,
        ...process.env,
      };
      return config;
    },
  },
});