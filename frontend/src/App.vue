// C:\Users\Vinay\Project\frontend\src\App.vue

<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref } from 'vue';
import { RouterView, useRouter, RouterLink, useRoute } from 'vue-router'; // <-- MODIFIED: Added useRoute
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notification';
import { debounce } from 'lodash-es';
import axiosInstance from '@/services/axiosInstance';
import type { User } from '@/stores/auth';
import { getAvatarUrl } from '@/utils/avatars';
import eventBus from './services/eventBus';

const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const router = useRouter();
const route = useRoute(); // <-- ADDED: Initialize route

// --- NEW: Click handler for the logo ---
function handleLogoClick(event: MouseEvent) {
  // If we are already on the home page ('/'),
  // prevent the default navigation and emit our custom event.
  if (route.path === '/') {
    event.preventDefault(); // Stop the RouterLink from navigating
    eventBus.emit('reset-feed-form');
  }
  // Otherwise, the RouterLink will navigate as normal.
}

// --- Search Autocomplete Logic (Unchanged) ---
const searchQuery = ref('');
const showSearchDropdown = ref(false);
const searchLoading = ref(false);
const searchResults = ref<User[]>([]);
const activeIndex = ref(-1);
const searchContainerRef = ref<HTMLDivElement | null>(null);

const handleFullSearchSubmit = () => {
  showSearchDropdown.value = false;
  if (searchQuery.value.trim()) {
    router.push({ name: 'search', query: { q: searchQuery.value.trim() } });
  }
};

const debouncedSearch = debounce(async (query: string) => {
  if (query.length < 1) {
    searchResults.value = [];
    return;
  }
  searchLoading.value = true;
  try {
    const response = await axiosInstance.get('/search/users/', {
      params: { q: query, page_size: 5 }
    });
    searchResults.value = response.data.results;
  } catch (error) {
    console.error("Search suggestions failed:", error);
    searchResults.value = [];
  } finally {
    searchLoading.value = false;
  }
}, 300);

const handleSearchInput = () => {
  if (searchQuery.value.trim()) {
    showSearchDropdown.value = true;
    activeIndex.value = -1;
    debouncedSearch(searchQuery.value);
  } else {
    showSearchDropdown.value = false;
    searchResults.value = [];
  }
};

const selectUserAndNavigate = (user: User) => {
  showSearchDropdown.value = false;
  searchQuery.value = ''; 
  router.push({ name: 'profile', params: { username: user.username } });
};

const handleSearchKeydown = (event: KeyboardEvent) => {
  if (!showSearchDropdown.value || searchResults.value.length === 0) return;

  if (event.key === 'ArrowDown') {
    event.preventDefault();
    activeIndex.value = (activeIndex.value + 1) % searchResults.value.length;
  } else if (event.key === 'ArrowUp') {
    event.preventDefault();
    activeIndex.value = (activeIndex.value - 1 + searchResults.value.length) % searchResults.value.length;
  } else if (event.key === 'Enter') {
    event.preventDefault();
    if (activeIndex.value !== -1) {
      selectUserAndNavigate(searchResults.value[activeIndex.value]);
    } else {
      handleFullSearchSubmit();
    }
  } else if (event.key === 'Escape') {
    showSearchDropdown.value = false;
  }
};

const closeSearchDropdownOnClickOutside = (event: MouseEvent) => {
  if (searchContainerRef.value && !searchContainerRef.value.contains(event.target as Node)) {
    showSearchDropdown.value = false;
  }
};
watch(showSearchDropdown, (isOpen) => {
  if (isOpen) document.addEventListener('click', closeSearchDropdownOnClickOutside);
  else document.removeEventListener('click', closeSearchDropdownOnClickOutside);
});
onUnmounted(() => document.removeEventListener('click', closeSearchDropdownOnClickOutside));

// --- Auth & Notification Logic (Unchanged) ---
onMounted(async () => {
  await authStore.initializeAuth();
  if (authStore.isAuthenticated) notificationStore.fetchUnreadCount();
});
watch(() => authStore.isAuthenticated, (newIsAuthenticated) => {
  if (newIsAuthenticated) notificationStore.fetchUnreadCount();
  else {
    notificationStore.unreadCount = 0;
    notificationStore.notifications = [];
  }
});
const handleLogout = async () => { await authStore.logout(); };
</script>

<template>
  <header class="bg-white shadow-sm sticky top-0 z-20">
    <nav class="container mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        
        <div class="flex-shrink-0">
          <!-- MODIFIED: @click now calls our new function -->
          <RouterLink to="/" @click="handleLogoClick" class="text-2xl font-bold tracking-tight transition-transform duration-300 hover:scale-105 inline-block">
            <span class="bg-gradient-to-r from-blue-600 to-purple-500 bg-clip-text text-transparent">NxtTurn</span>
          </RouterLink>
        </div>

        <!-- Center Section: Search Bar (Unchanged) -->
        <div class="flex-grow flex justify-center px-4" ref="searchContainerRef">
          <div class="relative w-full max-w-lg">
            <form @submit.prevent="handleFullSearchSubmit" v-if="authStore.isAuthenticated">
              <input 
                type="text"
                v-model="searchQuery"
                @input="handleSearchInput"
                @keydown="handleSearchKeydown"
                @focus="handleSearchInput"
                placeholder="Search for users..."
                class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-full bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
              />
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
              </div>
            </form>
            
            <div
              v-if="showSearchDropdown && searchQuery"
              class="absolute top-full mt-2 w-full rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-30"
            >
              <ul class="max-h-80 overflow-auto py-1 text-base">
                <li v-if="searchLoading" class="px-4 py-2 text-sm text-gray-500">Searching...</li>
                <li v-else-if="!searchLoading && searchResults.length === 0" class="px-4 py-2 text-sm text-gray-500">No users found.</li>
                
                <li v-for="(user, index) in searchResults" :key="user.id">
                  <a @click.prevent="selectUserAndNavigate(user)" href="#" class="flex items-center gap-3 px-4 py-2 text-sm cursor-pointer" :class="{ 'bg-blue-100': index === activeIndex }">
                    <img :src="getAvatarUrl(user.picture, user.first_name, user.last_name)" alt="avatar" class="w-8 h-8 rounded-full object-cover">
                    <div>
                      <span class="font-medium text-gray-900">{{ user.username }}</span>
                      <p class="text-gray-500 text-xs">{{ user.first_name }} {{ user.last_name }}</p>
                    </div>
                  </a>
                </li>
                 
                <li v-if="!searchLoading && searchResults.length > 0" class="border-t border-gray-200">
                    <button @click="handleFullSearchSubmit" class="w-full text-left px-4 py-2 text-sm font-medium text-blue-600 hover:bg-gray-100">
                      See all results for "{{ searchQuery }}"
                    </button>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Right Section: User Actions (Unchanged) -->
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
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
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