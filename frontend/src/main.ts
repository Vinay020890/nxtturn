// src/main.ts

import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

// 1. Import the Toast library and its CSS
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)

// Use Pinia for state management
app.use(createPinia())

// Use Vue Router for navigation
app.use(router)

// 2. Tell the app to use the Toast plugin
app.use(Toast)

// Mount the app to the DOM
app.mount('#app')