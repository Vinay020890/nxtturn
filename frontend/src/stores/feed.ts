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
  like_count: number; // Mandatory field from serializer
  comment_count?: number; // Optional if not always present
  is_liked_by_user: boolean; // Mandatory field from serializer

  // --- Fields needed for the new Like URL ---
  content_type_id: number; // The numeric ID for the ContentType model
  object_id: number;       // The numeric ID for this specific post object (should match 'id')
  // --- End of fields for Like URL ---

  // Optional frontend-only state for better UX
  isLiking?: boolean; // Flag to disable button during API call
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
          isLiking: false // Initialize flag
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
      const pageSize = fetchedPosts.length > 0 ? fetchedPosts.length : 10;
      totalPages.value = Math.ceil(response.data.count / pageSize);

    } catch (err: any) {
      console.error("FeedStore: Error fetching feed:", err);
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch feed.';
    } finally {
      isLoading.value = false;
      console.log("FeedStore: Fetch finished.");
    }
  }

    // REPLACE THE ENTIRE EXISTING createPost FUNCTION WITH THIS:
  async function createPost(content: string): Promise<Post | null> {
    console.log("FeedStore: Attempting to create post...");

    // Client-side check for empty content
    if (!content || content.trim().length === 0) {
      createPostError.value = "Post content cannot be empty.";
      console.error("FeedStore: Post content cannot be empty.");
      return null; // Indicate failure
    }

    isCreatingPost.value = true;    // Set loading state
    createPostError.value = null;   // Clear previous errors for this specific action

    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        createPostError.value = "User not authenticated. Please login to post.";
        console.warn("FeedStore: User not authenticated, cannot create post.");
        return null; // Indicate failure
      }

      // API endpoint for creating status posts
      const response = await axiosInstance.post<Post>('/posts/', {
        content: content
      });

      console.log("FeedStore: Post created successfully", response.data);

      // Optimistic Update: Prepend the new post
      // Ensure the new post has the 'isLiking' flag for consistency if your PostItem expects it
      posts.value.unshift({ ...response.data, isLiking: false });

      return response.data; // Return created post on success

    } catch (err: any) {
      console.error("FeedStore: Error creating post:", err);

      // Attempt to parse a more specific error message from the backend response
      if (err.response && err.response.data) {
          // Check for field-specific errors first (e.g., if 'content' field had an issue)
          if (err.response.data.content && Array.isArray(err.response.data.content) && err.response.data.content.length > 0) {
              createPostError.value = err.response.data.content.join(' ');
          } else if (typeof err.response.data.content === 'string') { // Django REST sometimes returns string for single field error
              createPostError.value = err.response.data.content;
          } else if (err.response.data.detail) { // Generic DRF error
              createPostError.value = err.response.data.detail;
          } else if (typeof err.response.data === 'string') { // Non-DRF string error
              createPostError.value = err.response.data;
          } else { // Fallback for other structured errors
              createPostError.value = "Failed to create post. Invalid input or server error.";
          }
      } else if (err.message) { // Network error or other client-side error
          createPostError.value = err.message;
      } else { // Ultimate fallback
          createPostError.value = 'An unexpected error occurred while creating the post.';
      }
      return null; // Indicate failure
    } finally {
      isCreatingPost.value = false; // Reset loading state
      console.log("FeedStore: Create post attempt finished.");
    }
  }

  // ========================================
  // === UPDATED toggleLike Action ===
  // ========================================
  async function toggleLike(postId: number) { // Accept postId for easier finding
    console.log(`FeedStore: Toggling like for post ID ${postId}`);

    const postIndex = posts.value.findIndex(p => p.id === postId);
    if (postIndex === -1) {
      console.error("FeedStore: Post to toggle not found in current feed state.");
      return;
    }

    // Get the actual post object
    const post = posts.value[postIndex];

    // Prevent rapid clicks if already processing
    if (post.isLiking) {
        console.log(`FeedStore: Like toggle already in progress for post ${postId}`);
        return;
    }
    post.isLiking = true; // Set flag to true

    const originalLikedStatus = post.is_liked_by_user;
    const originalLikeCount = post.like_count;

    // --- Optimistic Update ---
    post.is_liked_by_user = !originalLikedStatus;
    post.like_count += post.is_liked_by_user ? 1 : -1;
    // -------------------------

    try {
      // --- CONSTRUCT THE CORRECT URL ---
      // Use content_type_id and object_id from the post data
      const apiUrl = `/content/${post.content_type_id}/${post.object_id}/like/`;
      console.log(`FeedStore: Calling API: POST ${apiUrl}`);
      // ----------------------------------

      // --- Make the POST request ---
      const response = await axiosInstance.post<{ liked: boolean, like_count: number }>(apiUrl);
      // -----------------------------

      // --- Update with actual data from backend response ---
      // It's safer to use the response data to ensure consistency
      posts.value[postIndex].is_liked_by_user = response.data.liked;
      posts.value[postIndex].like_count = response.data.like_count;
      console.log(`FeedStore: Like toggled successfully for post ${postId}`, response.data);
      // -----------------------------------------------------

    } catch (err: any) {
      console.error(`FeedStore: Error toggling like for post ${postId}:`, err);
      // --- Revert Optimistic Update on Error ---
      // Check index again in case the post was removed while request was in flight
      if (posts.value[postIndex]?.id === postId) {
         posts.value[postIndex].is_liked_by_user = originalLikedStatus;
         posts.value[postIndex].like_count = originalLikeCount;
         console.log(`FeedStore: Reverted optimistic like state for post ${postId}`);
      }
      // Set general error state or re-throw if needed by component
      error.value = err.response?.data?.detail || err.message || 'Failed to toggle like.';
      // -----------------------------------------
    } finally {
      // --- Reset the isLiking flag ---
      // Check index again
      if (posts.value[postIndex]?.id === postId) {
         posts.value[postIndex].isLiking = false;
      }
       console.log(`FeedStore: Like toggle finished for post ${postId}`);
      // -------------------------------
    }
  }
  // ========================================


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
    // getters can be exposed here if defined
    fetchFeed,
    createPost,
    toggleLike
  };
});