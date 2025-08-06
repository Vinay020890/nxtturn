import { createRouter, createWebHistory } from 'vue-router';
import 'vue-router';
import { useAuthStore } from '@/stores/auth';
import CommunityLayout from '@/layouts/CommunityLayout.vue';
import ProfileLayout from '@/layouts/ProfileLayout.vue';
import ExploreLayout from '@/layouts/ExploreLayout.vue'; // <-- Import the new layout

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean;
    requiresGuest?: boolean;
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // --- ROUTE GROUP 1: Uses the 3-Column Community Layout ---
    {
      path: '/',
      component: CommunityLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'feed', component: () => import('@/views/FeedView.vue') },
        { path: 'groups', name: 'group-list', component: () => import('@/views/GroupListAllView.vue') },
        { path: 'groups/:slug', name: 'group-detail', component: () => import('@/views/GroupDetailView.vue') },
        { path: 'saved-posts', name: 'saved-posts', component: () => import('@/views/SavedPostsView.vue') },
        { path: 'notifications', name: 'notifications', component: () => import('@/views/NotificationsPage.vue') },
        { path: 'search', name: 'search', component: () => import('@/views/SearchPage.vue') },
        { path: 'posts/:postId', name: 'single-post', component: () => import('@/views/SinglePostView.vue') }
      ]
    },
    // --- ROUTE GROUP 2: Uses the Profile Layout ---
    {
      path: '/profile', 
      component: ProfileLayout,
      meta: { requiresAuth: true },
      children: [
        { 
          path: ':username',
          name: 'profile', 
          component: () => import('@/views/ProfileView.vue')
        }
      ]
    },
    // --- THIS IS THE NEW ROUTE FOR THE EXPLORE HUB ---
    {
      path: '/explore',
      component: ExploreLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'explore', component: () => import('@/views/ExploreView.vue') }
      ]
    },
    // --- Non-Layout Routes (Login/Register) ---
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { requiresGuest: true } },
    { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue'), meta: { requiresGuest: true } }
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