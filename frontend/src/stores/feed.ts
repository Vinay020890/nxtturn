// src/stores/feed.ts
import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import { useAuthStore } from './auth'; // May need auth status later

// Define the expected shape of an Author object from the API
interface PostAuthor {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  // profile_image_url?: string; // Add if you have it
}

// ==========================================
// === UPDATED Post Interface Definition ===
// ==========================================
export interface Post {
  id: number; // This should be the same as object_id
  post_type: string; // The model name string (e.g., 'statuspost', 'forumpost') from FeedItemSerializer
  author: PostAuthor;
  created_at: string; // Consider using Date object later
  updated_at: string;
  title: string | null; // Keep if ForumPosts have titles
  content: string;
  image: string | null;
  video: string | null;
  like_count: number; // Mandatory field from serializer
  comment_count?: number; // Optional if not always present
  is_liked_by_user: boolean; // Mandatory field from serializer

  // --- Fields needed for the new Like URL ---
  content_type_id: number; // The numeric ID for the ContentType model
  object_id: number;       // The numeric ID for this specific post object (should match 'id')
  // --- End of fields for Like URL ---

  // Optional frontend-only state for better UX
  isLiking?: boolean; // Flag to disable button during API call
  isDeleting?: boolean; 
}
// ==========================================

// Define the structure of the paginated response from the API
interface PaginatedFeedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Post[];
}

// Define the state structure for this store
interface FeedState {
  posts: Post[];
  isLoading: boolean;
  error: string | null;
  currentPage: number;
  totalPages: number;
  hasNextPage: boolean;
}

// Define the feed store using Setup Store syntax
export const useFeedStore = defineStore('feed', () => {
  // --- State ---
  const posts = ref<Post[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const currentPage = ref(1);
  const totalPages = ref(1);
  const hasNextPage = ref(false);

   

  // NEW: State for create post errors
  const createPostError = ref<string | null>(null);
  const isCreatingPost = ref(false); // NEW: For loading state during post creation

  const deletePostError = ref<string | null>(null);

  // DEFINE YOUR STANDARD PAGE SIZE HERE
  const ITEMS_PER_PAGE = 10; // Or whatever your backend pagination page_size is

  // --- Getters (Computed) ---
  // (Example: No active getters currently defined)

  // --- Actions ---

  // Action to fetch feed posts from the backend
  async function fetchFeed(page: number = 1) {
    if (isLoading.value) return;

    console.log(`FeedStore: Fetching feed page ${page}`);
    isLoading.value = true;
    error.value = null;

    if (page === 1) {
      posts.value = [];
    }

    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        console.warn("FeedStore: User not authenticated, aborting fetch.");
        isLoading.value = false;
        return;
      }

      const response = await axiosInstance.get<PaginatedFeedResponse>('/feed/', { // Use /api/feed/
        params: { page }
      });

      console.log("FeedStore: API response received", response.data);

      // Add isLiking flag to posts coming from API
      const fetchedPosts = response.data.results.map(post => ({
          ...post,
          isLiking: false, // Initialize flag
          isDeleting: false
      }));

      if (page === 1) {
          posts.value = fetchedPosts;
      } else {
          // For future infinite scroll: posts.value.push(...fetchedPosts);
          // For basic pagination, replace:
          posts.value = fetchedPosts;
      }

      currentPage.value = page;
      hasNextPage.value = response.data.next !== null;
      // const pageSize = fetchedPosts.length > 0 ? fetchedPosts.length : 10;
      // totalPages.value = Math.ceil(response.data.count / pageSize);
      // NEW CALCULATION:
      if (response.data.count > 0) {
        totalPages.value = Math.ceil(response.data.count / ITEMS_PER_PAGE);
      } else {
        totalPages.value = 1; // Or 0 if you prefer for an empty feed display
      }

    } catch (err: any) {
      console.error("FeedStore: Error fetching feed:", err);
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch feed.';
    } finally {
      isLoading.value = false;
      console.log("FeedStore: Fetch finished.");
    }
  }

  // REPLACE THE ENTIRE EXISTING createPost FUNCTION WITH THIS:
    // ---- START OF REPLACEMENT ----
  async function createPost(postData: FormData): Promise<Post | null> { // Parameter changed
    console.log("FeedStore: Attempting to create post with FormData...");

    isCreatingPost.value = true;
    createPostError.value = null; // Clear previous errors

    // Client-side validation for empty content/image is now primarily in CreatePostForm.vue
    // The backend serializer will perform the definitive validation.

    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        createPostError.value = "User not authenticated. Please login to post.";
        console.warn("FeedStore: User not authenticated, cannot create post.");
        // isCreatingPost.value = false; // Moved to finally block
        return null; // Still return null, but ensure isCreatingPost is handled in finally
      }

      // When sending FormData, Axios automatically sets Content-Type to multipart/form-data
      const response = await axiosInstance.post<Post>('/posts/', postData); // Send FormData directly

      console.log("FeedStore: Post created successfully", response.data);
      // Add the new post to the beginning of the posts array
      // Ensure the new post from API response has all necessary client-side flags like isLiking
      const newPostResponseData = { ...response.data, isLiking: false,isDeleting: false, image: response.data.image || null, video: response.data.video || null  }; // Ensure image is part of the new post object
      posts.value.unshift(newPostResponseData);

      return newPostResponseData; // Return created post object

    } catch (err: any) {
      console.error("FeedStore: Error creating post:", err);
      // Your existing improved error message parsing logic:
      if (err.response && err.response.data) {
          let specificErrorMessage = '';
          if (typeof err.response.data === 'object' && err.response.data !== null) {
              if (err.response.data.content && Array.isArray(err.response.data.content)) {
                  specificErrorMessage += err.response.data.content.join(' ') + ' ';
              }
              if (err.response.data.image && Array.isArray(err.response.data.image)) {
                  specificErrorMessage += err.response.data.image.join(' ') + ' ';
              }
              if (err.response.data.non_field_errors && Array.isArray(err.response.data.non_field_errors)) {
                  specificErrorMessage += err.response.data.non_field_errors.join(' ');
              } else if (err.response.data.detail && typeof err.response.data.detail === 'string') {
                  specificErrorMessage = err.response.data.detail;
              }
          }
          
          if (specificErrorMessage.trim()) {
              createPostError.value = specificErrorMessage.trim();
          } else if (typeof err.response.data === 'string') {
                createPostError.value = err.response.data;
          } else { 
              createPostError.value = "Failed to create post. Invalid input or server error.";
          }
      } else if (err.message) {
          createPostError.value = err.message;
      } else {
          createPostError.value = 'An unexpected error occurred while creating the post.';
      }
      return null; // Indicate failure
    } finally {
      isCreatingPost.value = false; // Reset loading state
      console.log("FeedStore: Create post attempt finished.");
    }
  }
  // ---- END OF REPLACEMENT ----
  // ========================================
  // === UPDATED toggleLike Action ===
  // ========================================
    // In frontend/src/stores/feed.ts
  // Replace the existing toggleLike function with this one:

  // Replace your ENTIRE existing toggleLike function with this:

async function toggleLike(
    postId: number,         // For optimistic UI update if post is in feedStore.posts
    postType: string,       // For optimistic UI update if post is in feedStore.posts
    contentTypeId: number,  // DIRECTLY USED for API call
    objectId: number        // DIRECTLY USED for API call (usually same as postId for StatusPost)
) {
  // console.log(`FeedStore: Attempting to toggle like for CTID: ${contentTypeId}, ObjID: ${objectId}. (Originating from PostID: ${postId}, Type: ${postType})`);

  // Attempt to find the post in the local feed state for optimistic UI updates
  const postIndex = posts.value.findIndex(p => p.id === postId && p.post_type === postType);
  let originalLikedStatus: boolean | undefined = undefined;
  let originalLikeCount: number | undefined = undefined;
  let localPostRef: Post | null = null; // Reference to the post in local state, if found

  if (postIndex !== -1) {
    localPostRef = posts.value[postIndex];
    if (localPostRef.isLiking) {
        // console.log(`FeedStore: Like toggle already in progress for post ${postId} in local feed state.`);
        // Decide if you want to return or let API call proceed (API might handle concurrency)
        // For now, let's return to prevent multiple optimistic updates if button is spammed
        return; 
    }
    localPostRef.isLiking = true;
    originalLikedStatus = localPostRef.is_liked_by_user;
    originalLikeCount = localPostRef.like_count;
    // Optimistic Update for local feed state
    localPostRef.is_liked_by_user = !localPostRef.is_liked_by_user;
    localPostRef.like_count += localPostRef.is_liked_by_user ? 1 : -1;
    // console.log(`FeedStore: Optimistically updated post ${postId} in local feed state.`);
  } else {
    // console.log(`FeedStore: Post ID ${postId}, Type ${postType} not found in local feed state. API call will proceed directly.`);
  }

  try {
    // ALWAYS use the passed-in contentTypeId and objectId for the API call
    const apiUrl = `/content/${contentTypeId}/${objectId}/like/`;
    console.log(`FeedStore: Calling API: POST ${apiUrl}`);
    
    const response = await axiosInstance.post<{ liked: boolean, like_count: number }>(apiUrl);
    // console.log(`FeedStore: API like toggle successful for object ${objectId}. Response:`, response.data);
    
    // If the post was found locally, update it with confirmed data from API
    if (localPostRef) { // Check if we had a local reference
        localPostRef.is_liked_by_user = response.data.liked;
        localPostRef.like_count = response.data.like_count;
        // console.log(`FeedStore: Confirmed API update for post ${postId} in local feed state.`);
    }
    // NOTE: If the post wasn't in feedStore.posts, this action has now updated the backend.
    // The profileStore's local update (triggered by PostItem.vue) will handle the UI on the profile page.
    // If the user navigates back to the main feed and that post is loaded, it will have the correct state from the server.

  } catch (err: any) {
    console.error(`FeedStore: Error toggling like for object ${objectId} via API:`, err);
    // Revert Optimistic Update on Error if it was done
    if (localPostRef && typeof originalLikedStatus === 'boolean' && typeof originalLikeCount === 'number') {
       localPostRef.is_liked_by_user = originalLikedStatus;
       localPostRef.like_count = originalLikeCount;
       console.log(`FeedStore: Reverted optimistic like state for post ${postId} in feedStore.`);
    }
    error.value = err.response?.data?.detail || err.message || 'Failed to toggle like.';
    throw err; // Re-throw so PostItem.vue's catch block can also handle it (e.g., show an alert)
  } finally {
    if (localPostRef) {
       localPostRef.isLiking = false;
    }
    // console.log(`FeedStore: Like toggle API call finished for object ${objectId}.`);
  }
}
// ========================================
  // ========================================

// ---- ADD THIS NEW ACTION ----
function incrementCommentCount(postId: number, postType: string) {
  console.log(`FeedStore: Attempting to increment comment count for Post ID: ${postId}, Type: ${postType}`);
  const postIndex = posts.value.findIndex(p => p.id === postId && p.post_type === postType);
  if (postIndex !== -1) {
    if (typeof posts.value[postIndex].comment_count === 'number') {
      posts.value[postIndex].comment_count!++; // Increment if it's already a number
    } else {
      posts.value[postIndex].comment_count = 1; // Initialize if it was undefined/null
    }
    console.log(`FeedStore: Incremented comment_count for post ${postId}. New count: ${posts.value[postIndex].comment_count}`);
  } else {
    console.warn(`FeedStore: Post ID ${postId} (Type: ${postType}) not found. Cannot increment comment count.`);
  }
}
// ---- END OF NEW ACTION ----

// ===========================================
  // === NEW deletePost ACTION ===
  // ===========================================
  async function deletePost(postId: number, postType: string): Promise<boolean> {
    console.log(`FeedStore: Attempting to delete post ID: ${postId}, Type: ${postType}`);
    deletePostError.value = null; // Clear previous delete errors

    const postIndex = posts.value.findIndex(p => p.id === postId && p.post_type === postType);
    let postToDelete: Post | null = null;

    if (postIndex !== -1) {
      postToDelete = posts.value[postIndex];
      if (postToDelete.isDeleting) {
        console.warn(`FeedStore: Delete operation already in progress for post ${postId}.`);
        return false; // Or throw an error if preferred
      }
      postToDelete.isDeleting = true; // Set loading state for this specific post
    } else {
      // If post is not in the current feed list (e.g., deleting from profile page directly affecting backend)
      // We can still proceed with the API call.
      // Or, you might decide this action only works on posts currently in the feed.
      // For now, let's allow API call even if not in local `posts` array.
      console.warn(`FeedStore: Post ID ${postId} (Type: ${postType}) not found in local feed state. Proceeding with API call.`);
    }

    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        deletePostError.value = "User not authenticated. Please login to delete posts.";
        console.warn("FeedStore: User not authenticated, cannot delete post.");
        if (postToDelete) postToDelete.isDeleting = false;
        return false;
      }

      // IMPORTANT: Construct the correct API endpoint.
      // Assuming 'statuspost' is the relevant post_type for direct deletion via /posts/<id>/
      // If you have other deletable post types with different base URLs, this needs adjustment.
      let apiUrl = '';
      if (postType.toLowerCase() === 'statuspost') { // Make sure this matches your post_type string
        apiUrl = `/posts/${postId}/`; // Ensure this matches your DRF URL for StatusPostRetrieveUpdateDestroyView
      } else {
        // Handle other post types or throw an error if only StatusPosts are deletable via this store action
        console.error(`FeedStore: Deletion for post_type '${postType}' is not configured.`);
        deletePostError.value = `Deletion for post type '${postType}' is not supported here.`;
        if (postToDelete) postToDelete.isDeleting = false;
        return false;
      }
      
      console.log(`FeedStore: Calling API: DELETE ${apiUrl}`);
      await axiosInstance.delete(apiUrl); // DELETE requests usually expect a 204 No Content response

      console.log(`FeedStore: Post ${postId} deleted successfully from backend.`);

      // If the post was found and deleted from local state
      if (postIndex !== -1) {
        posts.value.splice(postIndex, 1);
        console.log(`FeedStore: Post ${postId} removed from local feed state.`);
      }
      
      return true; // Indicate success

    } catch (err: any) {
      console.error(`FeedStore: Error deleting post ${postId}:`, err);
      if (err.response && err.response.data) {
        if (err.response.status === 403) {
             deletePostError.value = "You do not have permission to delete this post.";
        } else if (err.response.status === 404) {
            deletePostError.value = "Post not found. It might have already been deleted.";
        } else if (err.response.data.detail) {
            deletePostError.value = err.response.data.detail;
        } else {
            deletePostError.value = "Failed to delete post. Server error.";
        }
      } else if (err.message) {
        deletePostError.value = err.message;
      } else {
        deletePostError.value = 'An unexpected error occurred while deleting the post.';
      }
      if (postToDelete) postToDelete.isDeleting = false; // Reset loading state on error
      return false; // Indicate failure
    }
  }
  // ===========================================


  // --- Return exposed state, getters, and actions ---
  return {
    posts,
    isLoading,
    error,
    currentPage,
    totalPages,
    hasNextPage,

      // ADD THESE TWO LINES (can be anywhere within the return object):
    createPostError,    // The new error state for post creation
    isCreatingPost,     // The new loading state for post creation

    deletePostError,
    // getters can be exposed here if defined
    fetchFeed,
    createPost,
    toggleLike,
    incrementCommentCount, 
    deletePost,
  };
});