// src/stores/search.ts
import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import type { User } from '@/stores/auth';
import type { Post } from '@/stores/feed'; // <-- 1. IMPORT the Post type

// --- Interface for API Responses ---
interface PaginatedUserResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: User[];
}
// NEW: Interface for post search results
interface PaginatedPostResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Post[];
}

export const useSearchStore = defineStore('search', () => {
  // --- State ---
  const searchQuery = ref(''); 
  
  // State for User Search (renamed for clarity)
  const userResults = ref<User[]>([]);
  const isLoadingUsers = ref(false);
  const userError = ref<string | null>(null);

  // NEW: State for Content/Post Search
  const postResults = ref<Post[]>([]);
  const isLoadingPosts = ref(false);
  const postError = ref<string | null>(null);

  // --- Actions ---

  // This is the old searchUsers, now private
  async function _searchUsers(query: string) {
    isLoadingUsers.value = true;
    userError.value = null;
    try {
      const response = await axiosInstance.get<PaginatedUserResponse>('/search/users/', {
        params: { q: query }
      });
      userResults.value = response.data.results;
    } catch (err: any) {
      userError.value = err.response?.data?.detail || 'Failed to search for users.';
      userResults.value = [];
    } finally {
      isLoadingUsers.value = false;
    }
  }
  
  // NEW: Action to search for posts
  async function _searchPosts(query: string) {
    isLoadingPosts.value = true;
    postError.value = null;
    try {
      const response = await axiosInstance.get<PaginatedPostResponse>('/search/content/', {
        params: { q: query }
      });
      postResults.value = response.data.results;
    } catch (err: any) {
      postError.value = err.response?.data?.detail || 'Failed to search for content.';
      postResults.value = [];
    } finally {
      isLoadingPosts.value = false;
    }
  }

  // NEW: Master search action that runs both searches
  async function performSearch(query: string) {
    if (!query.trim()) {
      clearSearch();
      return;
    }
    searchQuery.value = query;

    // Run both searches concurrently for better performance
    await Promise.all([
      _searchUsers(query),
      _searchPosts(query)
    ]);
  }

  function clearSearch() {
    searchQuery.value = '';
    userResults.value = [];
    postResults.value = [];
    userError.value = null;
    postError.value = null;
  }

  return {
    // Shared State
    searchQuery,

    // User Search State & Results
    userResults,
    isLoadingUsers,
    userError,
    
    // Post Search State & Results
    postResults,
    isLoadingPosts,
    postError,

    // Actions
    performSearch,
    clearSearch,
  };
});