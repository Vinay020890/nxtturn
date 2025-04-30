import { createRouter, createWebHistory } from 'vue-router'
import 'vue-router';
import { useAuthStore } from '@/stores/auth';

// RegisterView is already imported, which is fine, but we'll use lazy loading below
// import RegisterView from '../views/RegisterView.vue';

// We removed the imports for HomeView and AboutView

// --- ADD THIS TYPE DECLARATION ---
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean // Indicates if authentication is required
    requiresGuest?: boolean // Indicates if the route is only for guests (unauthenticated users)
  }
}
// --- END OF TYPE DECLARATION ---

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
      component: () => import('../views/FeedView.vue'), // Points to the FeedView component
      meta: { requiresAuth: true }
    },
    // --- END OF FEED ROUTE ---

    // --- LOGIN ROUTE ---
    {
      path: '/login', // The URL path for the login page
      name: 'login',  // A unique name for this route (optional but good practice)
      // Lazy-load the component
      component: () => import('../views/LoginView.vue'),
      meta: { requiresGuest: true }
    },
    // --- END OF LOGIN ROUTE ---

    // --- ADD REGISTER ROUTE HERE ---
    {
      path: '/register', // The URL path for the registration page
      name: 'register', // A unique name for this route
      // Lazy-load the component for better performance
      component: () => import('../views/RegisterView.vue'),
      meta: { requiresGuest: true }
    },
    // --- END OF REGISTER ROUTE ---

    // --- ADD THE NEW PROFILE ROUTE ---
    {
      path: '/profile/:username', // Dynamic segment ':username'
      name: 'profile',
      // Lazy-load the component (we'll create ProfileView.vue next)
      component: () => import('@/views/ProfileView.vue'), // Use alias @
      // Let's allow anyone (logged in or not) to view profiles for now
      meta: { requiresAuth: false }
    },
    // --- END OF PROFILE ROUTE ---

    /*
    EXAMPLES of routes we might add later:
    ... (rest of your comments remain the same) ...
    */
  ],
})

// --- NAVIGATION GUARD LOGIC ---
router.beforeEach((to, from, next) => {
  // Get the auth store instance *inside* the guard
  // This ensures we get the latest state
  const authStore = useAuthStore();

  const requiresAuth = to.meta.requiresAuth;
  const requiresGuest = to.meta.requiresGuest;
  const isAuthenticated = authStore.isAuthenticated; // Check if user is logged in

  console.log(`Navigating to: ${to.path}, requiresAuth: ${requiresAuth}, requiresGuest: ${requiresGuest}, isAuthenticated: ${isAuthenticated}`); // Debug log

  if (requiresAuth && !isAuthenticated) {
    // Case 1: Route requires login, but user is not logged in
    console.log('Guard: Redirecting to login');
    next({ name: 'login' }); // Redirect to the login page
  } else if (requiresGuest && isAuthenticated) {
    // Case 2: Route requires guest (e.g., login/register), but user IS logged in
    console.log('Guard: Redirecting to feed');
    next({ name: 'feed' }); // Redirect authenticated users to the main feed page
  } else {
    // Case 3: No special requirements, or requirements met
    console.log('Guard: Allowing navigation');
    next(); // Allow navigation to proceed
  }
});
// --- END OF NAVIGATION GUARD LOGIC ---

// Export the router instance to be used in main.ts
export default router