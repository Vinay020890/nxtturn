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
      name: 'feed',
      component: () => import('@/views/FeedView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'), // Corrected filename
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'), // Corrected filename
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
    
  ],
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  const requiresAuth = to.meta.requiresAuth;
  const requiresGuest = to.meta.requiresGuest;
  const isAuthenticated = authStore.isAuthenticated;

  if (requiresAuth && !isAuthenticated) {
    next({ name: 'login' });
  } else if (requiresGuest && isAuthenticated) {
    next({ name: 'feed' });
  } else {
    next();
  }
});

export default router;