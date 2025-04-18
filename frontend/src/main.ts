import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)

// Use Pinia for state management
app.use(createPinia())

// Use Vue Router for navigation
app.use(router)

// Mount the app to the DOM
app.mount('#app')
