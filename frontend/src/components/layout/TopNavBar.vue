<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref, computed } from 'vue';
import { useRouter, RouterLink, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notification';
import { storeToRefs } from 'pinia';
import { debounce } from 'lodash-es';
import { getAvatarUrl } from '@/utils/avatars';
import type { User } from '@/stores/auth';
import type { Post } from '@/stores/feed';
import eventBus from '@/services/eventBus';
import { useSearchStore } from '@/stores/search';
import { useFeedStore } from '@/stores/feed';
import { useGroupStore } from '@/stores/group';

const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const searchStore = useSearchStore();
const feedStore = useFeedStore();
const groupStore = useGroupStore();
const router = useRouter();
const route = useRoute();

const { currentUser } = storeToRefs(authStore);
const { userResults, isLoadingUsers } = storeToRefs(searchStore);
const { searchResultsPosts: postResults, isLoadingSearchResults: isLoadingPosts } = storeToRefs(feedStore);
const { groupSearchResults: groupResults, isLoadingGroupSearch } = storeToRefs(groupStore);

const searchQuery = ref('');
const showSearchDropdown = ref(false);
const searchContainerRef = ref<HTMLDivElement | null>(null);

const hasAnyResults = computed(() => userResults.value.length > 0 || postResults.value.length > 0 || groupResults.value.length > 0);
const isSearching = computed(() => isLoadingUsers.value || isLoadingPosts.value || isLoadingGroupSearch.value);

function handleLogoClick(event: MouseEvent) {
  if (route.path === '/') {
    event.preventDefault();
    eventBus.emit('reset-feed-form');
  }
}

const handleFullSearchSubmit = () => {
  if (searchQuery.value.trim()) {
    showSearchDropdown.value = false;
    router.push({ name: 'search', query: { q: searchQuery.value.trim() } });
  }
};

const debouncedSearch = debounce(async (query: string) => {
  if (query.length < 1) {
    searchStore.clearSearch();
    feedStore.searchResultsPosts = [];
    return;
  }
  await Promise.all([
    searchStore.searchUsers(query),
    feedStore.searchPosts(query),
    groupStore.searchGroups(query)
  ]);
}, 300);

const handleSearchInput = () => {
  if (searchQuery.value.trim()) {
    showSearchDropdown.value = true;
    debouncedSearch(searchQuery.value);
  } else {
    showSearchDropdown.value = false;
    searchStore.clearSearch();
    feedStore.searchResultsPosts = [];
    groupStore.groupSearchResults = [];
  }
};

const selectUserAndNavigate = (user: User) => {
  showSearchDropdown.value = false;
  searchQuery.value = '';
  router.push({ name: 'profile', params: { username: user.username } });
};

const selectPostAndNavigate = (post: Post) => {
  showSearchDropdown.value = false;
  searchQuery.value = '';
  router.push({ name: 'single-post', params: { postId: post.id } });
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
  <header class="bg-white shadow-sm flex-shrink-0 z-40 fixed top-0 left-0 w-full">
    <nav class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        
        <div class="flex items-center gap-4">
          <RouterLink to="/" @click="handleLogoClick" class="text-2xl font-bold tracking-tight flex-shrink-0">
            <span class="bg-gradient-to-r from-blue-600 to-purple-500 bg-clip-text text-transparent">NxtTurn</span>
          </RouterLink>
          <div class="flex-grow flex justify-center px-4" ref="searchContainerRef">
            <div class="relative w-full max-w-lg">
              <!-- Search bar form and logic remains unchanged -->
              <form @submit.prevent="handleFullSearchSubmit" v-if="authStore.isAuthenticated">
                <input type="text" v-model="searchQuery" @input="handleSearchInput" @focus="handleSearchInput" placeholder="Search for users or content..." class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-full bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition" />
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                </div>
              </form>
              <!-- Search dropdown remains unchanged -->
              <div v-if="showSearchDropdown && searchQuery" class="absolute top-full mt-2 w-full rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
                <!-- ... dropdown content ... -->
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-4 flex-shrink-0">
          <template v-if="authStore.isAuthenticated">
            <!-- THIS IS THE CHANGE: Changed from <a> to <RouterLink> and added active-class -->
            <RouterLink :to="{ name: 'explore' }" class="text-sm font-medium text-gray-600 hover:text-indigo-500" active-class="text-indigo-600 font-semibold">Explore</RouterLink>
            
            <a href="#" class="text-sm font-medium text-gray-600 hover:text-indigo-500">Jobs</a>
            
            <!-- The rest of the user menu is unchanged -->
            <RouterLink :to="{ name: 'notifications' }" class="relative text-gray-600 hover:text-blue-500" title="Notifications">
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
              <span v-if="notificationStore.unreadCount > 0" class="absolute top-0 right-0 -mt-1 -mr-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">{{ notificationStore.unreadCount > 9 ? '9+' : notificationStore.unreadCount }}</span>
            </RouterLink>

            <RouterLink v-if="currentUser" :to="{ name: 'profile', params: { username: currentUser.username } }" class="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-blue-500">
              <img :src="getAvatarUrl(currentUser.picture, currentUser.first_name, currentUser.last_name)" alt="Your avatar" class="w-7 h-7 rounded-full object-cover">
              <span>Profile</span>
            </RouterLink>

            <button @click="handleLogout" class="text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-full transition">Logout</button>
          </template>
          <template v-else>
            <RouterLink to="/login" class="text-sm font-medium text-gray-600 hover:text-indigo-500">Login</RouterLink>
          </template>
        </div>
      </div>
    </nav>
  </header>
</template>