// src/stores/comment.ts

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';


// ... other imports if needed ...

// --- Define Comment structure ---
export interface CommentAuthor { // <-- ADD export
  id: number;
  username: string;
}

export interface Comment { // <-- Ensure this is exported
  id: number;
  author: CommentAuthor; // Uses the exported CommentAuthor
  content: string;
  created_at: string;
  updated_at: string;
}
// --- End Comment structure ---

// Define the store
export const useCommentStore = defineStore('comment', () => {
  // --- State ---
  const commentsByPost = ref<Record<string, Comment[]>>({});
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // --- Actions ---
  async function fetchComments(postType: string, objectId: number) {
    const postKey = `${postType}_${objectId}`;
    console.log(`CommentStore: Fetching comments for ${postKey}`);
    isLoading.value = true;
    error.value = null;

    try {
      const apiUrl = `/comments/${postType}/${objectId}/`;
      console.log(`CommentStore: Calling API: GET ${apiUrl}`);
      const response = await axiosInstance.get<Comment[]>(apiUrl);
      console.log(`CommentStore: Raw response.data:`, response.data);

      if (Array.isArray(response.data)) {
          commentsByPost.value[postKey] = response.data;
          console.log(`CommentStore: Stored ${response.data.length} comments for ${postKey}`);
      } else {
          console.error(`CommentStore: Received non-array data for comments ${postKey}:`, response.data);
          commentsByPost.value[postKey] = [];
      }
    } catch (err: any) {
      console.error(`CommentStore: Error fetching comments for ${postKey}:`, err);
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch comments.';
      delete commentsByPost.value[postKey];
    } finally {
      isLoading.value = false;
      console.log(`CommentStore: Fetch comments finished for ${postKey}`);
    }
  }

  // --- Return exposed state and actions --- VVVVVVVV ADD THIS VVVVVVVV
  return {
    commentsByPost,
    isLoading,
    error,
    fetchComments,
  };
  // --- END --- ^^^^^^^ ADD THIS ^^^^^^^

}); // This should be the final closing bracket/paren