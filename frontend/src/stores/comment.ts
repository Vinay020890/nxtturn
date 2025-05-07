// src/stores/comment.ts

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';

// --- Define Comment structure ---
export interface CommentAuthor {
  id: number;
  username: string;
}

export interface Comment {
  id: number;
  author: CommentAuthor;
  content: string;
  created_at: string;
  updated_at: string;
}
// --- End Comment structure ---

// Define the store
export const useCommentStore = defineStore('comment', () => {
  // --- State ---
  const commentsByPost = ref<Record<string, Comment[]>>({});
  const isLoading = ref(false); // Global loading for fetching comments
  const error = ref<string | null>(null); // Global error for fetching comments
  
  // Optional: Add specific state for creation if needed
  // const isCreatingComment = ref(false);
  // const createCommentError = ref<string | null>(null);

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

  // --- Action to create a new comment ---
  async function createComment(postType: string, objectId: number, content: string) {
    const postKey = `${postType}_${objectId}`;
    console.log(`CommentStore: Creating comment for ${postKey} with content: "${content}"`);

    // if (isCreatingComment.value) return; // Prevent multiple submissions if using specific loading state
    // isCreatingComment.value = true;
    // createCommentError.value = null;

    try {
      const apiUrl = `/comments/${postType}/${objectId}/`;
      console.log(`CommentStore: Calling API: POST ${apiUrl}`);
      const payload = { content: content };

      const response = await axiosInstance.post<Comment>(apiUrl, payload); 

      if (response.data && response.data.id) {
        console.log(`CommentStore: Comment created successfully for ${postKey}`, response.data);

        if (!Array.isArray(commentsByPost.value[postKey])) {
          commentsByPost.value[postKey] = [];
        }
        commentsByPost.value[postKey].unshift(response.data); // Add to the beginning

        return response.data; 
      } else {
        console.error(`CommentStore: Comment creation for ${postKey} succeeded but API returned invalid data`, response.data);
        throw new Error("Comment created, but received unexpected data from server.");
      }

    } catch (err: any) {
      console.error(`CommentStore: Error creating comment for ${postKey}:`, err);
      // If backend returns specific field errors for 'content':
      // const errorMessage = err.response?.data?.content?.[0] || err.response?.data?.detail || err.message || 'Failed to create comment.';
      // createCommentError.value = errorMessage;
      throw err; // Re-throw for component to handle
    } finally {
      // isCreatingComment.value = false;
      console.log(`CommentStore: Create comment attempt finished for ${postKey}`);
    }
  }
  // --- End of createComment action ---

  // --- Return exposed state and actions ---
  return {
    commentsByPost,
    isLoading,
    error,
    // isCreatingComment, // Expose if you add specific loading state
    // createCommentError, // Expose if you add specific error state
    fetchComments,
    createComment,     // <-- Make sure createComment is included here
  };

});