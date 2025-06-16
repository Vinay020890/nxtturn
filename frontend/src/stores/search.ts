// src/stores/search.ts
import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import type { User } from '@/stores/auth';

interface PaginatedUserResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: User[];
}

export const useSearchStore = defineStore('search', () => {
  const searchResults = ref<User[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  // CORRECTED: Use a consistent name
  const searchQuery = ref(''); 

  async function searchUsers(query: string) {
    if (!query.trim()) {
      clearSearch();
      return;
    }

    // CORRECTED: Update the consistently named ref
    searchQuery.value = query; 
    isLoading.value = true;
    error.value = null;

    try {
      const response = await axiosInstance.get<PaginatedUserResponse>('/search/users/', {
        params: { q: query }
      });
      searchResults.value = response.data.results;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to perform search.';
      searchResults.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  function clearSearch() {
    searchResults.value = [];
    searchQuery.value = ''; // CORRECTED
    error.value = null;
  }

  return {
    searchResults,
    isLoading,
    error,
    searchQuery, // CORRECTED: Export the consistently named ref
    searchUsers,
    clearSearch,
  };
});