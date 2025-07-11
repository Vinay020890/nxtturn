<script setup lang="ts">
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notification';
import { storeToRefs } from 'pinia';
import { computed } from 'vue';

// --- Initialize Stores ---
const authStore = useAuthStore();
const notificationStore = useNotificationStore();

// --- Get Reactive State from Stores ---
// Destructure reactive state for direct use in template
const { currentUser } = storeToRefs(authStore);
const { unreadCount } = storeToRefs(notificationStore);

// --- Computed property for notifications ---
const hasUnreadNotifications = computed(() => unreadCount.value > 0);

</script>

<template>
  <aside class="w-64 bg-white shadow-md pt-6 px-4 flex-shrink-0 min-h-screen">
    <div class="space-y-4">
      <h3 class="text-lg font-semibold text-gray-800">Main Navigation</h3>
      <ul class="space-y-2">
        <li>
          <RouterLink 
            :to="{ name: 'feed' }" 
            active-class="bg-blue-100 text-blue-700 font-semibold"
            class="flex items-center px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors"
          >
            <svg class="h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m0 0l7 7 7 7M19 10v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h.01"></path></svg>
            Feed
          </RouterLink>
        </li>
        <li>
          <RouterLink 
            :to="{ name: 'group-list' }" 
            active-class="bg-blue-100 text-blue-700 font-semibold"
            class="flex items-center px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors"
          >
            <svg class="h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h2a2 2 0 002-2V7a2 2 0 00-2-2h-2V3a1 1 0 00-1-1H7a1 1 0 00-1 1v2H4a2 2 0 00-2 2v11a2 2 0 002 2h2v-2a1 1 0 011-1h6a1 1 0 011 1v2zm0 0a2 2 0 002 2H5a2 2 0 00-2-2V7a2 2 0 00-2-2h-2V3a1 1 0 00-1-1H7a1 1 0 00-1 1v2H4a2 2 0 00-2 2v11a2 2 0 002 2h2v-2a1 1 0 011-1h6a1 1 0 011 1v2zm0 0a2 2 0 002 2h-2a2 2 0 00-2-2V7a2 2 0 00-2-2h-2V3a1 1 0 00-1-1H7a1 1 0 00-1 1v2H4a2 2 0 00-2 2v11a2 2 0 002 2h2v-2a1 1 0 011-1h6a1 1 0 011 1v2zm0 0a2 2 0 002 2h-2a2 2 0 00-2-2V7a2 2 0 00-2-2h-2V3a1 1 0 00-1-1H7a1 1 0 00-1 1v2H4a2 2 0 00-2 2v11a2 2 0 002 2h2v-2a1 1 0 011-1h6a1 1 0 011 1v2zm0 0a2 2 0 002 2H5a2 2 0 00-2-2V7a2 2 0 00-2-2h-2V3a1 1 0 00-1-1H7a1 1 0 00-1 1v2H4a2 2 0 00-2 2v11a2 2 0 002 2h2v-2a1 1 0 011-1h6a1 1 0 011 1v2z" /></svg>
            Groups
          </RouterLink>
        </li>
        <li>
          <RouterLink 
            :to="{ name: 'search' }" 
            active-class="bg-blue-100 text-blue-700 font-semibold"
            class="flex items-center px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors"
          >
            <svg class="h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            Search
          </RouterLink>
        </li>
        <li>
          <RouterLink 
            v-if="currentUser?.username"
            :to="{ name: 'profile', params: { username: currentUser.username } }" 
            active-class="bg-blue-100 text-blue-700 font-semibold"
            class="flex items-center px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors"
          >
            <svg class="h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
            My Profile
          </RouterLink>
        </li>
        <li>
          <RouterLink 
            :to="{ name: 'notifications' }" 
            active-class="bg-blue-100 text-blue-700 font-semibold"
            class="relative flex items-center px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors"
          >
            <svg class="h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
            Notifications
            <span v-if="hasUnreadNotifications" class="absolute top-1 right-2 flex items-center justify-center h-4 w-4 bg-red-500 text-white text-xs rounded-full">
              {{ unreadCount > 9 ? '9+' : unreadCount }}
            </span>
          </RouterLink>
        </li>
      </ul>

      <div class="mt-8 pt-4 border-t border-gray-200">
        <h3 class="text-lg font-semibold text-gray-800">Utilities</h3>
        <ul class="space-y-2">
          <li>
            <button 
              @click="authStore.logout()" 
              class="flex items-center w-full text-left px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors"
            >
              <svg class="h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
              Logout
            </button>
          </li>
        </ul>
      </div>
    </div>
  </aside>
</template>