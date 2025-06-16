<script setup lang="ts">
import { ref, onUnmounted, watch } from 'vue';
import { useSearchStore } from '@/stores/search';
import { storeToRefs } from 'pinia';
import { RouterLink, useRoute } from 'vue-router';
import { debounce } from 'lodash-es';

const searchStore = useSearchStore();
// CORRECTED: Import the consistently named ref
const { searchResults, isLoading, error, searchQuery } = storeToRefs(searchStore);
const route = useRoute();

const localQuery = ref((route.query.q as string) || '');

if (localQuery.value) {
  searchStore.searchUsers(localQuery.value);
}

watch(() => route.query.q, (newQuery) => {
  const queryStr = (newQuery as string) || '';
  localQuery.value = queryStr;
  searchStore.searchUsers(queryStr);
});

const debouncedSearch = debounce((query: string) => {
  searchStore.searchUsers(query);
}, 300);

const handleInput = (event: Event) => {
  const query = (event.target as HTMLInputElement).value;
  localQuery.value = query;
  debouncedSearch(query);
};

onUnmounted(() => {
  searchStore.clearSearch();
});
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-3xl font-bold text-gray-800 mb-6">Search Users</h1>

    <div class="relative">
      <input 
        type="text"
        v-model="localQuery"
        @input="handleInput"
        placeholder="Search for users by name or username..."
        class="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
      </div>
    </div>
    
    <div class="mt-6">
      <div v-if="isLoading" class="text-center py-6 text-gray-500">Searching...</div>
      <div v-else-if="error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
        <p>{{ error }}</p>
      </div>
      <ul v-else-if="searchResults.length > 0" class="bg-white rounded-lg shadow-md divide-y divide-gray-200">
        <li v-for="user in searchResults" :key="user.id">
          <RouterLink 
            :to="{ name: 'profile', params: { username: user.username } }" 
            class="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors"
          >
            <div class="w-12 h-12 bg-gray-300 rounded-full flex-shrink-0"></div>
            <div class="flex-grow">
              <p class="font-bold text-gray-800">{{ user.first_name }} {{ user.last_name }}</p>
              <p class="text-sm text-gray-500">@{{ user.username }}</p>
            </div>
          </RouterLink>
        </li>
      </ul>
      <!-- CORRECTED: Use the consistent name here -->
      <div v-else-if="searchQuery" class="text-center py-6 text-gray-500">
        No users found for "{{ searchQuery }}".
      </div>
    </div>
  </div>
</template>