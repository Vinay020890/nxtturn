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
  author: CommentAuthor;    // User who wrote the comment
  content: string;          // The text content of the comment
  created_at: string;       // Timestamp when created
  updated_at: string;       // Timestamp when last updated

  // Fields from the GenericForeignKey on the backend, linking to the commented object (e.g., StatusPost)
  content_type_id: number;  // ID of the ContentType model instance (e.g., for 'statuspost')
  object_id: number;        // ID of the related object (e.g., the StatusPost's ID)
  
  parent: number | null;    // <<<<------ ID of the parent comment if this is a reply, otherwise null

  // ---- 👇👇👇 ADD THESE NEW PROPERTIES 👇👇👇 ----
  like_count: number;
  is_liked_by_user: boolean;
  comment_content_type_id: number; // ContentType ID OF THE COMMENT ITSELF (for liking this comment)
  // ---- END OF NEW PROPERTIES ----
}

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

  // In frontend/src/stores/comment.ts
// Inside defineStore('comment', () => { ...

  async function createComment(
      postType: string, 
      objectId: number,         // ID of the main post (StatusPost, ForumPost, etc.)
      content: string, 
      parentPostActualId: number, // The actual ID of the main post for updating feed/profile store counts
      parentCommentId?: number    // <<<< NEW: Optional ID of the comment being replied to
  ) {
    const postKey = `${postType}_${objectId}`; // Key for the main post's comments
    console.log(
      `CommentStore: Creating comment for ${postKey} (MainPostActualID: ${parentPostActualId}). ` +
      (parentCommentId ? `Reply to CommentID: ${parentCommentId}` : 'Top-level comment.') +
      ` Content: "${content}"`
    );

    isCreatingComment.value = true;
    createCommentError.value = null;

    try {
      const apiUrl = `/comments/${postType}/${objectId}/`; 
      
      const payload: { content: string; parent?: number } = { content: content };
      if (parentCommentId) {
        payload.parent = parentCommentId; // Add parent ID to payload if it's a reply
      }
      console.log('CommentStore: Payload for comment creation:', payload);

      const response = await axiosInstance.post<Comment>(apiUrl, payload);

      if (response.data && response.data.id) {
        const newComment = response.data;
        console.log(`CommentStore: Comment/Reply created successfully for ${postKey}`, newComment);        
        if (!Array.isArray(commentsByPost.value[postKey])) {
          commentsByPost.value[postKey] = [];
        }
        commentsByPost.value[postKey].unshift(newComment);

        // Update comment counts in other stores
        try {
          const feedStore = useFeedStore();
          // Ensure incrementCommentCount handles postType correctly if needed for finding the post
          feedStore.incrementCommentCount(parentPostActualId, postType); 
          console.log(`CommentStore: Incremented comment_count in feedStore for post ${parentPostActualId}`);
        } catch (storeError) {
           console.error(`CommentStore: Error updating feedStore count for post ${parentPostActualId}:`, storeError);
        }

        try {
          const profileStore = useProfileStore();
          // Ensure this action exists and handles postType correctly if needed
          profileStore.incrementCommentCountInUserPosts(parentPostActualId, postType); 
          console.log(`CommentStore: Incremented comment_count in profileStore for post ${parentPostActualId}`);
        } catch (storeError) {
           console.error(`CommentStore: Error updating profileStore count for post ${parentPostActualId}:`, storeError);
        }

        return newComment;
      } else {
        console.error(`CommentStore: Comment creation for ${postKey} succeeded but API returned invalid data`, response.data);
        throw new Error("Comment created, but received unexpected data from server.");
      }

    } catch (err: any) {
      console.log("<<<<< INSIDE CORRECTED CATCH BLOCK (comment.ts) >>>>>"); 
      console.error(`CommentStore: Error creating comment/reply for ${postKey}:`, err);
      
      if (err.response && err.response.data) {
        const dataContent = err.response.data.content;
        const dataParent = err.response.data.parent; 
        const dataNonField = err.response.data.non_field_errors;
        const dataDetail = err.response.data.detail;

        let errorMessages: string[] = [];

        if (dataContent && Array.isArray(dataContent)) { 
          errorMessages = errorMessages.concat(dataContent);
        }
        if (dataParent && Array.isArray(dataParent)) { 
          errorMessages = errorMessages.concat(dataParent);
        }
        if (dataNonField && Array.isArray(dataNonField)) {
            errorMessages = errorMessages.concat(dataNonField);
        }
        
        if (errorMessages.length > 0) {
          createCommentError.value = errorMessages.join(' ');
        } else if (dataDetail && typeof dataDetail === 'string') {
          createCommentError.value = dataDetail;
        } else if (typeof err.response.data === 'string') { // For plain string errors
            createCommentError.value = err.response.data;
        } else { 
          console.error('CommentStore: Unhandled backend error data structure:', err.response.data);
          createCommentError.value = "An unexpected error occurred. Please check details.";
        }
      } else {
        createCommentError.value = err.message || 'Failed to create comment/reply.';
      }
      console.log(`CommentStore: Set createCommentError to: "${createCommentError.value}"`);
      throw err; 
    } finally {
      isCreatingComment.value = false; 
      console.log(`CommentStore: Create comment/reply attempt finished for ${postKey}`);
    }
  }

// Make sure this function is within the defineStore callback and before the return statement.
// Also ensure useFeedStore and useProfileStore are imported at the top of comment.ts if not already.
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

  // ---- 👇👇👇 THIS IS THE NEW ACTION FUNCTION 👇👇👇 ----
  async function toggleLikeOnComment(
    commentId: number,
    commentContentTypeId: number, // The ContentType ID of the Comment model itself
    parentPostType: string,       // e.g., 'statuspost' (to find the comment in local state)
    parentObjectId: number        // e.g., 1 (ID of the statuspost, to find the comment in local state)
  ) {
    const postKey = `${parentPostType}_${parentObjectId}`;
    
    const commentsList = commentsByPost.value[postKey];
    if (!commentsList) {
      console.error(`CommentStore: No comments loaded for post ${postKey} to toggle like for comment ${commentId}.`);
      // Optionally throw an error or display a message to the user
      return; 
    }

    const commentIndex = commentsList.findIndex(c => c.id === commentId);

    if (commentIndex === -1) {
      console.error(`CommentStore: Comment with ID ${commentId} not found in store for post ${postKey} to toggle like.`);
      return; 
    }

    try {
      console.log(`CommentStore: Toggling like for comment ID ${commentId} (ContentTypeID for Comment model: ${commentContentTypeId}) on post ${postKey}`);
      // Ensure your API base URL is handled by axiosInstance correctly (e.g., includes /api/)
      const response = await axiosInstance.post<{ liked: boolean; like_count: number }>(
        `/content/${commentContentTypeId}/${commentId}/like/`
      );

      if (response.status === 200) {
        const { liked, like_count } = response.data;
        // Update the specific comment in the store
        commentsByPost.value[postKey][commentIndex].is_liked_by_user = liked;
        commentsByPost.value[postKey][commentIndex].like_count = like_count;
        console.log(`CommentStore: Comment ID ${commentId} like status updated to ${liked}, count ${like_count}`);
      } else {
        console.error('CommentStore: Failed to toggle like on comment, API responded with status:', response.status);
      }
    } catch (error: any) {
      console.error('CommentStore: Error toggling like on comment API call:', error);
      // It's good practice to re-throw the error so the component can be notified and potentially update the UI (e.g., show an alert)
      throw error; 
    }
  }
  // ---- 👆👆👆 END OF THE NEW ACTION FUNCTION 👆👆👆 ----

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
    toggleLikeOnComment,
  };

});