// src/stores/feed.ts
import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import { useAuthStore } from './auth'; // May need auth status later

// Define the expected shape of a Post object from the API
// (Adjust based on your actual serializer output seen in the API test)
interface PostAuthor {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  // profile_image_url?: string; // Add if you have it
}

interface Post {
  id: number;
  post_type: string; // e.g., 'statuspost', 'forumpost'
  author: PostAuthor;
  created_at: string; // Consider using Date object later
  updated_at: string;
  title: string | null;
  content: string;
  // Add other fields you expect: like_count, comment_count, is_liked_by_user, etc.
  like_count?: number;
  comment_count?: number;
  is_liked_by_user?: boolean;
}

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

// Define the feed store
export const useFeedStore = defineStore('feed', () => {
  // --- State ---
  const posts = ref<Post[]>([]); // Holds the posts for the current view
  const isLoading = ref(false);   // Tracks loading state
  const error = ref<string | null>(null); // Stores any error message
  const currentPage = ref(1);     // Tracks the current page number
  const totalPages = ref(1);      // Total pages available
  const hasNextPage = ref(false); // Indicates if there's a next page

  // --- Getters (Computed) ---
  // Example: Maybe filter posts later?
  // const statusPosts = computed(() => posts.value.filter(p => p.post_type === 'statuspost'));

  // --- Actions ---
  // Action to fetch the feed will be added here

  // --- Return ---
  // Expose state, getters, and actions

  // --- Actions ---

// Action to fetch feed posts from the backend
async function fetchFeed(page: number = 1) {
    // Don't fetch if already loading
    if (isLoading.value) return;
  
    console.log(`FeedStore: Fetching feed page ${page}`);
    isLoading.value = true;
    error.value = null; // Clear previous errors
  
    // If fetching the first page, clear existing posts
    // If fetching subsequent pages (for infinite scroll later), we would append
    if (page === 1) {
      posts.value = [];
    }
  
    try {
      // Get auth token status - needed to ensure user is logged in?
      // Although axiosInstance handles sending the token, we might prevent
      // fetch attempts if the user logs out while feed is loading.
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        console.warn("FeedStore: User not authenticated, aborting fetch.");
        // Optionally set an error message or handle appropriately
        isLoading.value = false;
        return;
      }
  
      // Make the API call using the page parameter
      const response = await axiosInstance.get<PaginatedFeedResponse>('/feed/', {
        params: { page } // Send page number as query parameter
      });
  
      console.log("FeedStore: API response received", response.data);
  
      // Update state with data from the response
      // Append posts for infinite scroll, replace for first page load
      if (page === 1) {
          posts.value = response.data.results;
      } else {
          // For future infinite scroll: posts.value.push(...response.data.results);
          // For basic pagination, we might just replace: posts.value = response.data.results;
          // Let's stick with replacing for now for simplicity
           posts.value = response.data.results;
      }
  
  
      // Update pagination state
      currentPage.value = page;
      hasNextPage.value = response.data.next !== null; // Check if 'next' URL exists
      // Calculate total pages (optional but useful)
      const pageSize = response.data.results.length > 0 ? response.data.results.length : 10; // Use actual results length or default page size
      totalPages.value = Math.ceil(response.data.count / pageSize);
  
  
    } catch (err: any) {
      console.error("FeedStore: Error fetching feed:", err);
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch feed.';
      // Clear posts on error? Optional, depends on desired UX
      // posts.value = [];
    } finally {
      // This always runs, regardless of success or error
      isLoading.value = false; // Set loading state back to false
      console.log("FeedStore: Fetch finished.");
    }
  } // --- End of fetchFeed function ---


  // Action to create a new status post
async function createPost(content: string) {
    // Note: We might want a separate loading/error state for creation later
    console.log("FeedStore: Attempting to create post...");
  
    // Basic validation (could also be done in component)
    if (!content || content.trim().length === 0) {
      console.error("FeedStore: Post content cannot be empty.");
      throw new Error("Post content cannot be empty."); // Throw error to component
    }
  
    try {
      // Get auth store to ensure user is logged in
      // (axios interceptor handles token, but this prevents unnecessary calls)
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        console.warn("FeedStore: User not authenticated, cannot create post.");
        throw new Error("User not authenticated.");
      }
  
      // Make the POST request to the backend endpoint for creating StatusPosts
      // Ensure '/posts/' matches the URL defined in community/urls.py for StatusPostListCreateView
      const response = await axiosInstance.post<Post>('/posts/', {
        content: content // Send the content in the request body
      });
  
      console.log("FeedStore: Post created successfully", response.data);
  
      // --- Strategy after successful post creation ---
      // Option 1: Re-fetch the first page of the feed to show the new post
      // await fetchFeed(1); // Uncomment this line to refresh the feed
  
      // Option 2: (More advanced - Optimistic Update) Prepend the new post to the local state
       posts.value.unshift(response.data); // Add the new post to the beginning of the array
                                           // Make sure the API returns the created Post object!
  
      // Let's use Option 2 (unshift) for now for better UX, assuming API returns the post
      return response.data; // Return the created post data
  
    } catch (err: any) {
      console.error("FeedStore: Error creating post:", err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create post.';
      // We don't update the main feed 'error' state here,
      // as that's for fetch errors. We throw instead.
      throw new Error(errorMessage); // Throw error for the component to handle
    } finally {
      // Reset creation-specific loading state if we add one later
      console.log("FeedStore: Create post attempt finished.");
    }
  } // --- End of createPost function ---
  

  // --- ADD THIS ACTION ---
// Action to toggle like status for a post
async function toggleLike(postToToggle: Post) {
    console.log(`FeedStore: Toggling like for post ID ${postToToggle.id}`);
  
    // Find the index of the post in the current state array
    const postIndex = posts.value.findIndex(p => p.id === postToToggle.id && p.post_type === postToToggle.post_type);
    if (postIndex === -1) {
      console.error("FeedStore: Post to toggle not found in current feed state.");
      return; // Or throw error?
    }
  
    // --- Optimistic Update (Optional but good UX) ---
    // Immediately update the local state before waiting for the API response.
    // Store the original values in case we need to revert on error.
    const originalLiked = posts.value[postIndex].is_liked_by_user;
    const originalCount = posts.value[postIndex].like_count ?? 0; // Handle undefined count
  
    // Toggle liked status and adjust count locally
    posts.value[postIndex].is_liked_by_user = !originalLiked;
    posts.value[postIndex].like_count = originalLiked ? originalCount - 1 : originalCount + 1;
    // --- End of Optimistic Update ---
  
  
    try {
      // Prepare API request data
      const contentType = postToToggle.post_type.toLowerCase(); // e.g., 'statuspost'
      const objectId = postToToggle.id;
      const url = `/${contentType}/${objectId}/like/`; // Construct the URL
  
      // Call the backend toggle endpoint
      const response = await axiosInstance.post<{ liked: boolean, like_count: number }>(url);
  
      // --- Update with actual API response (Verify Optimistic) ---
      // It's good practice to update the state with the exact values
      // returned by the API to ensure consistency.
      posts.value[postIndex].is_liked_by_user = response.data.liked;
      posts.value[postIndex].like_count = response.data.like_count;
      console.log(`FeedStore: Like toggled successfully for post ${objectId}`, response.data);
      // --- End of API response update ---
  
    } catch (err: any) {
      console.error(`FeedStore: Error toggling like for post ${postToToggle.id}:`, err);
  
      // --- Revert Optimistic Update on Error ---
      if (postIndex !== -1) { // Check index again just in case
         posts.value[postIndex].is_liked_by_user = originalLiked;
         posts.value[postIndex].like_count = originalCount;
      }
      // --- End of Revert ---
  
      // Optionally set a general error state or re-throw
      // error.value = err.response?.data?.detail || err.message || 'Failed to toggle like.';
      // For now, just logging the error and reverting is sufficient
    } finally {
      // Optional: Add loading state specific to this post ID if needed
    }
  } // --- End of toggleLike function ---
  


  return {
    posts,
    isLoading,
    error,
    currentPage,
    totalPages,
    hasNextPage,
    // statusPosts, // Expose getters if defined
    fetchFeed, // Action will be added and exposed later
    createPost,
    toggleLike
  };
});