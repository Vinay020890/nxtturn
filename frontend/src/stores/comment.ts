// src/stores/comment.ts

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import { useFeedStore } from '@/stores/feed'; // <-- Import feed store
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

  // --- Action to create a new comment ---
  // ADD parentPostId argument
  async function createComment(postType: string, objectId: number, content: string, parentPostId: number) {
    const postKey = `${postType}_${objectId}`;
    console.log(`CommentStore: Creating comment for ${postKey} (Parent Post ID: ${parentPostId}) with content: "${content}"`);

    isCreatingComment.value = true; // <-- SET LOADING STATE
    createCommentError.value = null; // <-- CLEAR PREVIOUS CREATION ERROR

    try {
      const apiUrl = `/comments/${postType}/${objectId}/`;
      console.log(`CommentStore: Calling API: POST ${apiUrl}`);
      const payload = { content: content };

      const response = await axiosInstance.post<Comment>(apiUrl, payload);

      if (response.data && response.data.id) {
        console.log(`CommentStore: Comment created successfully for ${postKey}`, response.data);

        // Add the new comment to the beginning of the list for this post
        if (!Array.isArray(commentsByPost.value[postKey])) {
          commentsByPost.value[postKey] = [];
        }
        commentsByPost.value[postKey].unshift(response.data); // Add to the beginning

        // --- Update Feed Store Count ---
        try {
          const feedStore = useFeedStore();
          const feedPostIndex = feedStore.posts.findIndex(p => p.id === parentPostId);
          if (feedPostIndex !== -1) {
            feedStore.posts[feedPostIndex].comment_count = (feedStore.posts[feedPostIndex].comment_count ?? 0) + 1;
            console.log(`CommentStore: Incremented comment_count in feedStore for post ${parentPostId}`);
          } else {
            // console.warn(`CommentStore: Parent post ${parentPostId} not found in feedStore.`); // Optional log
          }
        } catch (storeError) {
           console.error(`CommentStore: Error updating feedStore count for post ${parentPostId}:`, storeError);
        }
        // --- End Update Feed Store Count ---

        // --- Update Profile Store Count ---
        try {
          const profileStore = useProfileStore(); // Get profile store instance
          if (profileStore.userPosts && profileStore.userPosts.length > 0) {
              const profilePostIndex = profileStore.userPosts.findIndex(p => p.id === parentPostId);
              if (profilePostIndex !== -1) {
                profileStore.userPosts[profilePostIndex].comment_count = (profileStore.userPosts[profilePostIndex].comment_count ?? 0) + 1;
                console.log(`CommentStore: Incremented comment_count in profileStore for post ${parentPostId}`);
              } else {
                 // console.warn(`CommentStore: Parent post ${parentPostId} not found in profileStore.`); // Optional log
              }
          }
        } catch (storeError) {
           console.error(`CommentStore: Error updating profileStore count for post ${parentPostId}:`, storeError);
        }
        // --- End Update Profile Store Count ---

        return response.data; // Return the created comment
      } else {
        console.error(`CommentStore: Comment creation for ${postKey} succeeded but API returned invalid data`, response.data);
        throw new Error("Comment created, but received unexpected data from server.");
      }

    } catch (err: any) {
      console.log("<<<<< INSIDE CORRECTED CATCH BLOCK >>>>>"); // THE DEBUG LOG
      console.error(`CommentStore: Error creating comment for ${postKey}:`, err);
      // Try to get more specific error messages
      if (err.response && err.response.data) {
        if (err.response.data.content && Array.isArray(err.response.data.content)) {
          createCommentError.value = err.response.data.content.join(' '); 
        } else if (err.response.data.detail) {
          createCommentError.value = err.response.data.detail; // This should catch "Simulated backend error..."
        } else {
          // Log the whole data object if detail/content not found
          console.error('CommentStore: Backend error data structure:', err.response.data);
          createCommentError.value = "An unexpected error occurred while posting the comment. Check console.";
        }
      } else {
        createCommentError.value = err.message || 'Failed to create comment.';
      }
      console.log(`CommentStore: Set createCommentError to: "${createCommentError.value}"`); // THE DEBUG LOG
      throw err; 
    } finally {
      isCreatingComment.value = false; 
      console.log(`CommentStore: Create comment attempt finished for ${postKey}`);
    }
  }
  // --- End of createComment action ---

  // --- Action to delete a comment ---
async function deleteComment(commentId: number, postType: string, objectId: number, parentPostId: number) {
  const postKey = `${postType}_${objectId}`;
  console.log(`CommentStore: Attempting to delete comment ID ${commentId} from post ${postKey} (Parent Post ID: ${parentPostId})`);

  // Optional: Add a specific loading state for deletion if needed
  // const isDeletingComment = ref(false); // Example
  // isDeletingComment.value = true;

  try {
    // Construct the API URL for deleting a specific comment
    // This should match your backend's CommentRetrieveUpdateDestroyAPIView URL for a specific comment pk
    const apiUrl = `/comments/${commentId}/`; 
    console.log(`CommentStore: Calling API: DELETE ${apiUrl}`);

    await axiosInstance.delete(apiUrl); // Make the DELETE request

    console.log(`CommentStore: Comment ID ${commentId} deleted successfully from backend.`);

    // --- Remove the comment from the local store state ---
    if (commentsByPost.value[postKey]) {
      commentsByPost.value[postKey] = commentsByPost.value[postKey].filter(c => c.id !== commentId);
      console.log(`CommentStore: Removed comment ID ${commentId} from local state for ${postKey}.`);
    }

    // --- Decrement comment count in feedStore ---
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

    // --- Decrement comment count in profileStore ---
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
    
    return true; // Indicate success

  } catch (err: any) {
    console.error(`CommentStore: Error deleting comment ID ${commentId}:`, err);
    // Set a generic error or a specific deletion error state if you add one
    // error.value = err.response?.data?.detail || err.message || 'Failed to delete comment.';
    throw err; // Re-throw for the component to handle if needed
  } finally {
    // isDeletingComment.value = false; // If using specific loading state
    console.log(`CommentStore: Delete comment attempt finished for comment ID ${commentId}.`);
  }
}
// --- End of deleteComment action ---

// --- Action to edit an existing comment ---
async function editComment(commentId: number, newContent: string, postType: string, objectId: number) {
  const postKey = `${postType}_${objectId}`;
  console.log(`CommentStore: Attempting to edit comment ID ${commentId} for post ${postKey} with new content: "${newContent}"`);

  // Optional: Add specific loading/error states for editing if desired
  // isEditingComment.value = true; 
  // editCommentError.value = null;

  try {
    // API URL for updating a specific comment
    const apiUrl = `/comments/${commentId}/`; 
    console.log(`CommentStore: Calling API: PUT ${apiUrl}`); // Or PATCH

    // Payload only needs the content, as other fields shouldn't be changed by user edit
    const payload = { content: newContent };

    // Make the PUT request (or PATCH if you prefer partial updates)
    // The backend should return the updated comment object.
    const response = await axiosInstance.put<Comment>(apiUrl, payload); 

    if (response.data && response.data.id) {
      console.log(`CommentStore: Comment ID ${commentId} edited successfully on backend.`, response.data);

      // --- Update the comment in the local store state ---
      if (commentsByPost.value[postKey]) {
        const commentIndex = commentsByPost.value[postKey].findIndex(c => c.id === commentId);
        if (commentIndex !== -1) {
          // Replace the old comment object with the updated one from the response
          commentsByPost.value[postKey][commentIndex] = response.data;
          console.log(`CommentStore: Updated comment ID ${commentId} in local state for ${postKey}.`);
        } else {
          console.warn(`CommentStore: Edited comment ID ${commentId} not found in local state for ${postKey} to update.`);
        }
      }
      return response.data; // Return the updated comment
    } else {
      console.error(`CommentStore: Comment edit for ${commentId} API call succeeded but returned invalid data`, response.data);
      // editCommentError.value = "Comment edited, but received unexpected data from server.";
      throw new Error("Comment edited, but received unexpected data from server.");
    }

  } catch (err: any) {
    console.error(`CommentStore: Error editing comment ID ${commentId}:`, err);
    // if (err.response && err.response.data) { ... handle specific errors ... }
    // editCommentError.value = err.response?.data?.detail || err.response?.data?.content?.join(' ') || err.message || 'Failed to edit comment.';
    throw err; // Re-throw for the component
  } finally {
    // isEditingComment.value = false;
    console.log(`CommentStore: Edit comment attempt finished for comment ID ${commentId}.`);
  }
}
// --- End of editComment action ---

  // --- Return exposed state and actions ---
  return {
    commentsByPost,
    isLoading,
    error,
    fetchComments,
    createComment, // <-- Make sure createComment is included here
    isCreatingComment,
    createCommentError,
    deleteComment,
    editComment,
  };

});