// src/stores/comment.ts

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import { useFeedStore } from '@/stores/feed'; // <-- Import feed store

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
  // ADD parentPostId argument
  async function createComment(postType: string, objectId: number, content: string, parentPostId: number) {
    const postKey = `${postType}_${objectId}`;
    console.log(`CommentStore: Creating comment for ${postKey} (Parent Post ID: ${parentPostId}) with content: "${content}"`);

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

        // --- ADDED LOGIC TO UPDATE FEED STORE COUNT ---
        try {
          const feedStore = useFeedStore(); // Get feed store instance
          // Note: This assumes the post is in the main feedStore. If called from ProfileView,
          // you might need to update profileStore similarly or use a more robust event system.
          const postIndex = feedStore.posts.findIndex(p => p.id === parentPostId); // Find the parent post by its ID
          if (postIndex !== -1) {
            // Increment the comment count directly on the post object in the feed store
            feedStore.posts[postIndex].comment_count = (feedStore.posts[postIndex].comment_count ?? 0) + 1;
            console.log(`CommentStore: Incremented comment_count in feedStore for post ${parentPostId}`);
          } else {
            console.warn(`CommentStore: Parent post ${parentPostId} not found in feedStore to update count.`);
            // TODO: Need to handle updating comment count for posts shown on ProfileView via profileStore
          }
        } catch (storeError) {
           console.error(`CommentStore: Error updating feedStore count for post ${parentPostId}:`, storeError);
        }
        // --- END LOGIC TO UPDATE FEED STORE COUNT ---

        return response.data;
      } else {
        console.error(`CommentStore: Comment creation for ${postKey} succeeded but API returned invalid data`, response.data);
        throw new Error("Comment created, but received unexpected data from server.");
      }

    } catch (err: any) {
      console.error(`CommentStore: Error creating comment for ${postKey}:`, err);
      throw err; // Re-throw for component
    } finally {
      console.log(`CommentStore: Create comment attempt finished for ${postKey}`);
    }
  }
  // --- End of createComment action ---

  // --- Return exposed state and actions ---
  return {
    commentsByPost,
    isLoading,
    error,
    fetchComments,
    createComment, // <-- Make sure createComment is included here
  };

});