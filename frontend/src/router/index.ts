import { createRouter, createWebHistory } from 'vue-router'
// RegisterView is already imported, which is fine, but we'll use lazy loading below
// import RegisterView from '../views/RegisterView.vue';

// We removed the imports for HomeView and AboutView

const router = createRouter({
  // This uses the browser's history API for clean URLs (no #)
  history: createWebHistory(import.meta.env.BASE_URL),

  // The 'routes' array defines the pages of our application.
  routes: [

     // --- FEED ROUTE ---
     {
      path: '/', // The root path of the application
      name: 'feed', // Name for programmatic navigation
      // Lazy-load the component for better performance
      component: () => import('../views/FeedView.vue') // Points to the FeedView component
    },
    // --- END OF FEED ROUTE ---

    // --- LOGIN ROUTE ---
    {
      path: '/login', // The URL path for the login page
      name: 'login',  // A unique name for this route (optional but good practice)
      // Lazy-load the component
      component: () => import('../views/LoginView.vue')
    },
    // --- END OF LOGIN ROUTE ---

    // --- ADD REGISTER ROUTE HERE ---
    {
      path: '/register', // The URL path for the registration page
      name: 'register', // A unique name for this route
      // Lazy-load the component for better performance
      component: () => import('../views/RegisterView.vue')
    },
    // --- END OF REGISTER ROUTE ---

    /*
    EXAMPLES of routes we might add later:
    ... (rest of your comments remain the same) ...
    */
  ],
})

// Export the router instance to be used in main.ts
export default router