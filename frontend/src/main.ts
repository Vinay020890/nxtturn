import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

// --- ADD THIS IMPORT ---
import GoogleSignInPlugin from 'vue3-google-signin'
// ----------------------

import App from './App.vue'
import router from './router'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)

if (window.Cypress) {
  window.pinia = pinia
}

app.use(router)
app.use(Toast)

// --- ADD THIS BLOCK ---
app.use(GoogleSignInPlugin, {
  clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID,
})
// ----------------------

app.mount('#app')
