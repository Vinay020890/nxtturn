<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref, computed } from 'vue';
import { useRouter, RouterLink, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notification';
import { storeToRefs } from 'pinia';
import { debounce } from 'lodash-es';
import { getAvatarUrl } from '@/utils/avatars';
import type { User } from '@/stores/auth';
import { useSearchStore } from '@/stores/search';
import { useFeedStore } from '@/stores/feed';
import { useGroupStore } from '@/stores/group';
import { usePostsStore, type Post } from '@/stores/posts';
import eventBus from '@/services/eventBus';

const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const searchStore = useSearchStore();
const feedStore = useFeedStore();
const groupStore = useGroupStore();
const postsStore = usePostsStore();
const router = useRouter();
const route = useRoute();

const { unreadCount } = storeToRefs(notificationStore);
const { currentUser } = storeToRefs(authStore);
const { userResults, isLoadingUsers } = storeToRefs(searchStore);

const { isLoadingSearchResults: isLoadingPosts } = storeToRefs(feedStore);
const postResultIds = computed(() => feedStore.searchResultPostIds);
const postResults = computed(() => postsStore.getPostsByIds(postResultIds.value));

const { groupSearchResults: groupResults, isLoadingGroupSearch } = storeToRefs(groupStore);

const searchQuery = ref('');
const showSearchDropdown = ref(false);
const searchContainerRef = ref<HTMLDivElement | null>(null);

const hasAnyResults = computed(() => userResults.value.length > 0 || postResults.value.length > 0 || groupResults.value.length > 0);
const isSearching = computed(() => isLoadingUsers.value || isLoadingPosts.value || isLoadingGroupSearch.value);

function handleLogoClick(event: MouseEvent) {
  if (route.path === '/') {
    event.preventDefault();
    eventBus.emit('scroll-to-top');
  }
}

// --- NEW FUNCTION for Profile Link ---
function handleProfileClick(event: MouseEvent) {
  // Only scrolls to top if on your own profile page
  if (route.name === 'profile' && route.params.username === currentUser.value?.username) {
    event.preventDefault();
    eventBus.emit('scroll-profile-to-top');
  }
}

// --- NEW FUNCTION for Notifications Link ---
function handleNotificationsClick(event: MouseEvent) {
  if (route.name === 'notifications') {
    event.preventDefault();
    eventBus.emit('scroll-notifications-to-top');
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
    feedStore.searchResultPostIds = [];
    groupStore.groupSearchResults = [];
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
    feedStore.searchResultPostIds = [];
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

onMounted(() => {
  authStore.initializeAuth();
});

const handleLogout = async () => { await authStore.logout(); };
</script>

<template>
  <header class="bg-white shadow-sm flex-shrink-0 z-40 fixed top-0 left-0 w-full">
    <nav class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex-shrink-0">
          <RouterLink to="/" @click="handleLogoClick" class="text-2xl font-bold tracking-tight">
            <span class="bg-gradient-to-r from-blue-600 to-purple-500 bg-clip-text text-transparent">NxtTurn</span>
          </RouterLink>
        </div>
        <div class="flex-grow flex justify-center px-4" ref="searchContainerRef">
          <!-- ... Search Form ... -->
        </div>
        <div class="flex items-center gap-4 flex-shrink-0">
          <template v-if="authStore.isAuthenticated">
            <RouterLink :to="{ name: 'explore' }" class="text-sm font-medium text-gray-600 hover:text-indigo-500" active-class="text-indigo-600 font-semibold">Explore</RouterLink>
            <a href="#" class="text-sm font-medium text-gray-600 hover:text-indigo-500">Jobs</a>
            <RouterLink :to="{ name: 'notifications' }" @click="handleNotificationsClick" class="relative text-gray-600 hover:text-blue-500" title="Notifications">
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
              <span 
                v-if="unreadCount > 0" 
                data-cy="notification-indicator"
                class="absolute top-0 right-0 -mt-1 -mr-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white"
              >
                {{ unreadCount > 9 ? '9+' : unreadCount }}
              </span>
            </RouterLink>
            <RouterLink v-if="currentUser" :to="{ name: 'profile', params: { username: currentUser.username } }" @click="handleProfileClick" class="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-blue-500" data-cy="profile-link">
              <img :src="getAvatarUrl(currentUser.picture, currentUser.first_name, currentUser.last_name)" alt="Your avatar" class="w-7 h-7 rounded-full object-cover">
              <span>Profile</span>
            </RouterLink>
            <button @click="handleLogout" class="text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-full transition" data-cy="logout-button">Logout</button>
          </template>
          <template v-else>
            <RouterLink to="/login" class="text-sm font-medium text-gray-600 hover:text-indigo-500">Login</RouterLink>
          </template>
        </div>
      </div>
    </nav>
  </header>
</template>