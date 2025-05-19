// C:\Users\Vinay\Project\frontend\src\stores\comment.ts

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import { useFeedStore } from '@/stores/feed';
import { useProfileStore } from '@/stores/profile';

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
  const isCreatingComment = ref(false);
  const createCommentError = ref<string | null>(null);

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

  async function createComment(postType: string, objectId: number, content: string, parentPostId: number) {
    const postKey = `${postType}_${objectId}`;
    console.log(`CommentStore: Creating comment for ${postKey} (Parent Post ID: ${parentPostId}) with content: "${content}"`);

    isCreatingComment.value = true;
    createCommentError.value = null;

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
        commentsByPost.value[postKey].unshift(response.data);

        try {
          const feedStore = useFeedStore();
          const feedPostIndex = feedStore.posts.findIndex(p => p.id === parentPostId);
          if (feedPostIndex !== -1) {
            feedStore.posts[feedPostIndex].comment_count = (feedStore.posts[feedPostIndex].comment_count ?? 0) + 1;
            console.log(`CommentStore: Incremented comment_count in feedStore for post ${parentPostId}`);
          }
        } catch (storeError) {
           console.error(`CommentStore: Error updating feedStore count for post ${parentPostId}:`, storeError);
        }

        try {
          const profileStore = useProfileStore();
          if (profileStore.userPosts && profileStore.userPosts.length > 0) {
              const profilePostIndex = profileStore.userPosts.findIndex(p => p.id === parentPostId);
              if (profilePostIndex !== -1) {
                profileStore.userPosts[profilePostIndex].comment_count = (profileStore.userPosts[profilePostIndex].comment_count ?? 0) + 1;
                console.log(`CommentStore: Incremented comment_count in profileStore for post ${parentPostId}`);
              }
          }
        } catch (storeError) {
           console.error(`CommentStore: Error updating profileStore count for post ${parentPostId}:`, storeError);
        }
        return response.data;
      } else {
        console.error(`CommentStore: Comment creation for ${postKey} succeeded but API returned invalid data`, response.data);
        throw new Error("Comment created, but received unexpected data from server.");
      }

    } catch (err: any) {
      console.log("<<<<< INSIDE CORRECTED CATCH BLOCK >>>>>"); 
      console.error(`CommentStore: Error creating comment for ${postKey}:`, err);
      
      if (err.response && err.response.data) {
        // +++ START NEW MINIMAL DEBUG LOGS +++
        const dataContent = err.response.data.content;
        const isDataContentArray = Array.isArray(dataContent);
        console.log(`CommentStore DEBUG: err.response.data.content IS:`, dataContent);
        console.log(`CommentStore DEBUG: Array.isArray(err.response.data.content) IS: ${isDataContentArray}`);
        // +++ END NEW MINIMAL DEBUG LOGS +++

        if (dataContent && isDataContentArray) { // Using the variables for clarity
          console.log("CommentStore: Path A - Extracting from err.response.data.content"); 
          createCommentError.value = dataContent.join(' '); 
        } else if (err.response.data.detail) {
          console.log("CommentStore: Path B - Extracting from err.response.data.detail"); 
          createCommentError.value = err.response.data.detail;
        } else { 
          console.error('CommentStore: Path C - Backend error data structure (FALLBACK):', err.response.data);
          createCommentError.value = "An unexpected error occurred while posting the comment. Check console.";
        }
      } else {
        console.log("CommentStore: Path D - err.response or err.response.data is missing");
        createCommentError.value = err.message || 'Failed to create comment.';
      }
      console.log(`CommentStore: Set createCommentError to: "${createCommentError.value}"`);
      throw err; 
    } finally {
      isCreatingComment.value = false; 
      console.log(`CommentStore: Create comment attempt finished for ${postKey}`);
    }
  }

  async function deleteComment(commentId: number, postType: string, objectId: number, parentPostId: number) {
    const postKey = `${postType}_${objectId}`;
    console.log(`CommentStore: Attempting to delete comment ID ${commentId} from post ${postKey} (Parent Post ID: ${parentPostId})`);

    try {
      const apiUrl = `/comments/${commentId}/`; 
      console.log(`CommentStore: Calling API: DELETE ${apiUrl}`);
      await axiosInstance.delete(apiUrl);
      console.log(`CommentStore: Comment ID ${commentId} deleted successfully from backend.`);

      if (commentsByPost.value[postKey]) {
        commentsByPost.value[postKey] = commentsByPost.value[postKey].filter(c => c.id !== commentId);
        console.log(`CommentStore: Removed comment ID ${commentId} from local state for ${postKey}.`);
      }

      try {
        const feedStore = useFeedStore();
        const feedPostIndex = feedStore.posts.findIndex(p => p.id === parentPostId);
        if (feedPostIndex !== -1) {
          feedStore.posts[feedPostIndex].comment_count = Math.max(0, (feedStore.posts[feedPostIndex].comment_count ?? 0) - 1);
          console.log(`CommentStore: Decremented comment_count in feedStore for post ${parentPostId}`);
        }
      } catch (storeError) {
         console.error(`CommentStore: Error updating feedStore count for post ${parentPostId}:`, storeError);
      }

      try {
        const profileStore = useProfileStore();
        if (profileStore.userPosts && profileStore.userPosts.length > 0) {
            const profilePostIndex = profileStore.userPosts.findIndex(p => p.id === parentPostId);
            if (profilePostIndex !== -1) {
              profileStore.userPosts[profilePostIndex].comment_count = Math.max(0, (profileStore.userPosts[profilePostIndex].comment_count ?? 0) - 1);
              console.log(`CommentStore: Decremented comment_count in profileStore for post ${parentPostId}`);
            }
        }
      } catch (storeError) {
         console.error(`CommentStore: Error updating profileStore count for post ${parentPostId}:`, storeError);
      }
      
      return true;

    } catch (err: any) {
      console.error(`CommentStore: Error deleting comment ID ${commentId}:`, err);
      throw err; 
    } finally {
      console.log(`CommentStore: Delete comment attempt finished for comment ID ${commentId}.`);
    }
  }

  async function editComment(commentId: number, newContent: string, postType: string, objectId: number) {
    const postKey = `${postType}_${objectId}`;
    console.log(`CommentStore: Attempting to edit comment ID ${commentId} for post ${postKey} with new content: "${newContent}"`);

    try {
      const apiUrl = `/comments/${commentId}/`; 
      console.log(`CommentStore: Calling API: PUT ${apiUrl}`);
      const payload = { content: newContent };
      const response = await axiosInstance.put<Comment>(apiUrl, payload); 

      if (response.data && response.data.id) {
        console.log(`CommentStore: Comment ID ${commentId} edited successfully on backend.`, response.data);

        if (commentsByPost.value[postKey]) {
          const commentIndex = commentsByPost.value[postKey].findIndex(c => c.id === commentId);
          if (commentIndex !== -1) {
            commentsByPost.value[postKey][commentIndex] = response.data;
            console.log(`CommentStore: Updated comment ID ${commentId} in local state for ${postKey}.`);
          } else {
            console.warn(`CommentStore: Edited comment ID ${commentId} not found in local state for ${postKey} to update.`);
          }
        }
        return response.data;
      } else {
        console.error(`CommentStore: Comment edit for ${commentId} API call succeeded but returned invalid data`, response.data);
        throw new Error("Comment edited, but received unexpected data from server.");
      }

    } catch (err: any) {
      console.error(`CommentStore: Error editing comment ID ${commentId}:`, err);
      throw err;
    } finally {
      console.log(`CommentStore: Edit comment attempt finished for comment ID ${commentId}.`);
    }
  }

  return {
    commentsByPost,
    isLoading,
    error,
    fetchComments,
    createComment,
    isCreatingComment,
    createCommentError,
    deleteComment,
    editComment,
  };

});