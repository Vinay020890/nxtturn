import { createRouter, createWebHistory } from 'vue-router';
import 'vue-router';
import { useAuthStore } from '@/stores/auth';

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean;
    requiresGuest?: boolean;
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'feed', // <-- NOTE: The name for your feed is 'feed', not 'home'
      component: () => import('@/views/FeedView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/profile/:username',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: false } 
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('@/views/NotificationsPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/SearchPage.vue'),
      meta: { requiresAuth: true }
    },
    // --- ADD THIS NEW ROUTE OBJECT ---
    {
      path: '/posts/:postId',
      name: 'single-post',
      component: () => import('@/views/SinglePostView.vue'),
      meta: { requiresAuth: true }
    },
    // --- END OF NEW ROUTE ---
  ],
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  // Initialize the store to ensure isAuthenticated is correctly loaded from localStorage
  // This is a common pattern to call initializeAuth here, but let's assume App.vue handles it.
  
  const requiresAuth = to.meta.requiresAuth;
  const requiresGuest = to.meta.requiresGuest;
  const isAuthenticated = authStore.isAuthenticated;

  if (requiresAuth && !isAuthenticated) {
    next({ name: 'login' });
  } else if (requiresGuest && isAuthenticated) {
    // Your existing logic correctly redirects logged-in users from login/register to the feed.
    next({ name: 'feed' });
  } else {
    next();
  }
});

export default router;