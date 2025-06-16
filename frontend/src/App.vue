<script setup lang="ts">
import { onMounted, watch, ref } from 'vue';
import { RouterView, useRouter, RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notification';

const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const router = useRouter();

// --- State for the header search bar ---
const searchQuery = ref('');

const handleSearchSubmit = () => {
  if (searchQuery.value.trim()) {
    // Navigate to the search page with the query, which will then perform the search
    router.push({ name: 'search', query: { q: searchQuery.value.trim() } });
    // We can choose to clear it or leave the text there. Let's clear it for now.
    searchQuery.value = ''; 
  }
};

onMounted(async () => {
  await authStore.initializeAuth();
  if (authStore.isAuthenticated) {
    notificationStore.fetchUnreadCount();
  }
});

watch(
  () => authStore.isAuthenticated,
  (newIsAuthenticated) => {
    if (newIsAuthenticated) {
      notificationStore.fetchUnreadCount();
    } else {
      notificationStore.unreadCount = 0;
      notificationStore.notifications = [];
    }
  }
);

const handleLogout = async () => {
  await authStore.logout();
  router.push({ name: 'login' });
};
</script>

<template>
  <header class="bg-white shadow-sm sticky top-0 z-20">
    <nav class="container mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        
        <!-- Left Section: Logo -->
        <div class="flex-shrink-0">
          <RouterLink to="/" class="text-2xl font-bold text-gray-800">nxtturn</RouterLink>
        </div>

        <!-- Center Section: Search Bar (visible on larger screens) -->
        <div class="flex-grow flex justify-center px-4">
           <form @submit.prevent="handleSearchSubmit" v-if="authStore.isAuthenticated" class="relative w-full max-w-lg">
            <input 
              type="text"
              v-model="searchQuery"
              placeholder="Search..."
              class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-full bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
            />
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            </div>
          </form>
        </div>

        <!-- Right Section: User Actions -->
        <div class="flex items-center gap-4 flex-shrink-0">
          <template v-if="authStore.isAuthenticated">
            
            <RouterLink 
              v-if="authStore.currentUser?.username"
              :to="{ name: 'profile', params: { username: authStore.currentUser.username } }" 
              class="text-sm font-medium text-gray-600 hover:text-blue-500 transition-colors"
            >
              My Profile
            </RouterLink>

            <RouterLink 
              :to="{ name: 'notifications' }" 
              class="relative text-gray-600 hover:text-blue-500 transition-colors"
              title="Notifications"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
              <span v-if="notificationStore.unreadCount > 0" class="absolute top-0 right-0 -mt-1 -mr-1 flex items-center justify-center h-5 w-5 bg-red-500 text-white text-xs rounded-full">
                {{ notificationStore.unreadCount > 9 ? '9+' : notificationStore.unreadCount }}
              </span>
            </RouterLink>

            <button @click="handleLogout" class="text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-full transition">
              Logout
            </button>
          </template>

          <template v-else>
            <RouterLink to="/login" class="text-sm font-medium text-gray-600 hover:text-blue-500 transition-colors">Login</RouterLink>
          </template>
        </div>
      </div>
    </nav>
  </header>

  <main class="py-6">
    <RouterView />
  </main>
</template>