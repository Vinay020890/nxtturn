import { createRouter, createWebHistory } from 'vue-router'

// We removed the imports for HomeView and AboutView

const router = createRouter({
  // This uses the browser's history API for clean URLs (no #)
  history: createWebHistory(import.meta.env.BASE_URL),

  // The 'routes' array defines the pages of our application.
  // It's currently empty because we deleted the example views.
  // We will add our application's routes here later.
  routes: [
    /*
    EXAMPLES of routes we might add later:

    {
      path: '/', // The root URL, maybe for the feed?
      name: 'feed',
      // Use dynamic import for lazy loading components
      component: () => import('../views/FeedView.vue') // We need to create FeedView.vue
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue') // We need to create LoginView.vue
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue') // We need to create RegisterView.vue
    },
    {
      path: '/profile/:username', // Route with a dynamic parameter
      name: 'profile',
      component: () => import('../views/ProfileView.vue'), // We need to create ProfileView.vue
      props: true // Pass route params as props to the component
    }
    */
  ],
})

// Export the router instance to be used in main.ts
export default router
