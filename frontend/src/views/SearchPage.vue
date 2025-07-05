<script setup lang="ts">
import { ref, onUnmounted, watch, computed } from 'vue';
import { useSearchStore } from '@/stores/search';
import { storeToRefs } from 'pinia';
import { useRoute, useRouter } from 'vue-router'; // <-- Import useRouter
import { debounce } from 'lodash-es';
import PostItem from '@/components/PostItem.vue'; // <-- 1. IMPORT PostItem
import { getAvatarUrl } from '@/utils/avatars'; // <-- Import avatar utility

const searchStore = useSearchStore();
const route = useRoute();
const router = useRouter(); // <-- Initialize router

// --- 2. UPDATE to use new store properties ---
const { 
  searchQuery,
  userResults, 
  isLoadingUsers, 
  userError,
  postResults,
  isLoadingPosts,
  postError
} = storeToRefs(searchStore);

const localQuery = ref((route.query.q as string) || '');
const activeTab = ref<'users' | 'posts'>('users'); // State for the active tab

// --- 3. Initial Search on Page Load ---
if (localQuery.value) {
  // Call the new master search action
  searchStore.performSearch(localQuery.value);
}

// --- 4. Watch for URL Query Changes ---
watch(() => route.query.q, (newQuery) => {
  const queryStr = (newQuery as string) || '';
  if (localQuery.value !== queryStr) {
    localQuery.value = queryStr;
    searchStore.performSearch(queryStr);
  }
});

// --- 5. Debounced Search from Input ---
const debouncedSearch = debounce((query: string) => {
  // Update the URL to reflect the search query
  router.push({ name: 'search', query: { q: query } });
  // The watcher above will trigger the actual search
}, 500);

const handleInput = (event: Event) => {
  const query = (event.target as HTMLInputElement).value;
  localQuery.value = query;
  if (query.trim()) {
    debouncedSearch(query);
  } else {
    // If input is cleared, clear the results and URL
    searchStore.clearSearch();
    router.push({ name: 'search' });
  }
};

onUnmounted(() => {
  // Optional: you might want to keep search results when navigating away and back
  // searchStore.clearSearch();
});
</script>

<template>
  <div class="max-w-4xl mx-auto p-4">
    <h1 class="text-3xl font-bold text-gray-800 mb-6">Search</h1>

    <!-- Search Input Bar -->
    <div class="relative mb-6">
      <input 
        type="text"
        v-model="localQuery"
        @input="handleInput"
        placeholder="Search for users or content..."
        class="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
      </div>
    </div>
    
    <!-- Tabs for Users and Posts -->
    <div class="border-b border-gray-200 mb-6">
      <nav class="-mb-px flex space-x-8" aria-label="Tabs">
        <button 
          @click="activeTab = 'users'"
          :class="['whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm', activeTab === 'users' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300']"
        >
          Users
        </button>
        <button 
          @click="activeTab = 'posts'"
          :class="['whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm', activeTab === 'posts' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300']"
        >
          Posts
        </button>
      </nav>
    </div>

    <!-- Search Results Section -->
    <div>
      <!-- Users Tab Content -->
      <div v-if="activeTab === 'users'">
        <div v-if="isLoadingUsers" class="text-center py-6 text-gray-500">Searching for users...</div>
        <div v-else-if="userError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4"><p>{{ userError }}</p></div>
        <ul v-else-if="userResults.length > 0" class="bg-white rounded-lg shadow-md divide-y divide-gray-200">
          <li v-for="user in userResults" :key="user.id">
            <router-link :to="{ name: 'profile', params: { username: user.username } }" class="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors">
              <img :src="getAvatarUrl(user.picture, user.first_name, user.last_name)" alt="avatar" class="w-12 h-12 rounded-full object-cover bg-gray-200 flex-shrink-0">
              <div class="flex-grow">
                <p class="font-bold text-gray-800">{{ user.first_name }} {{ user.last_name }}</p>
                <p class="text-sm text-gray-500">@{{ user.username }}</p>
              </div>
            </router-link>
          </li>
        </ul>
        <div v-else-if="searchQuery" class="text-center py-6 text-gray-500">No users found for "{{ searchQuery }}".</div>
      </div>

      <!-- Posts Tab Content -->
      <div v-if="activeTab === 'posts'">
        <div v-if="isLoadingPosts" class="text-center py-6 text-gray-500">Searching for posts...</div>
        <div v-else-if="postError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4"><p>{{ postError }}</p></div>
        <div v-else-if="postResults.length > 0" class="space-y-6">
          <PostItem v-for="post in postResults" :key="post.id" :post="post" />
        </div>
        <div v-else-if="searchQuery" class="text-center py-6 text-gray-500">No posts found for "{{ searchQuery }}".</div>
      </div>
    </div>
  </div>
</template>