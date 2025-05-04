// src/stores/profile.ts
import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import type { Post } from '@/stores/feed'; // Import Post type for user posts
import { useAuthStore } from '@/stores/auth';

// Define interface for the User Profile data structure
// (Based on UserProfileSerializer output)
export interface UserProfile {
  username: string;
  first_name: string;
  last_name: string;
  date_joined: string; // Or Date
  bio: string | null;
  location_city: string | null;
  location_state: string | null;
  college_name: string | null;
  major: string | null;
  graduation_year: number | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  skills: string[]; // Array of strings
  interests: string[]; // Array of strings
  profile_picture_url: string | null;
  updated_at: string; // Or Date
  is_followed_by_request_user: boolean;
}

// Define the state structure
interface ProfileState {
  currentProfile: UserProfile | null;
  userPosts: Post[];
  isLoadingProfile: boolean;
  isLoadingPosts: boolean;
  errorProfile: string | null;
  errorPosts: string | null;
  // Add pagination state for user posts if needed later
}

// Define the profile store using Setup Store syntax
export const useProfileStore = defineStore('profile', () => {
  
  const authStoreInstance = useAuthStore(); // Get auth store instance

  // --- State ---
  
  const currentProfile = ref<UserProfile | null>(null);
  const userPosts = ref<Post[]>([]);
  const isLoadingProfile = ref(false);
  const isLoadingPosts = ref(false);
  const errorProfile = ref<string | null>(null);
  const errorPosts = ref<string | null>(null);

  // --- ADD THIS BLOCK ---
  const postsPagination = ref({
    count: 0, // Total number of posts the user has
    next: null as string | null, // URL for the next page (if any)
    previous: null as string | null, // URL for the previous page (if any)
    currentPage: 1, // The page number we are currently viewing
    totalPages: 1, // How many pages total (we'll calculate this)
    pageSize: 10 // How many posts per page (matches backend default)
});
// --- END OF BLOCK TO ADD ---

  const isFollowing = ref(false);
  const isLoadingFollow = ref(false);

  // --- Actions ---

  // Action to fetch profile details
  async function fetchProfile(username: string) {
    console.log(`ProfileStore: Fetching profile for ${username}`);
    isLoadingProfile.value = true;
    errorProfile.value = null;
    currentProfile.value = null; // Clear previous profile
    isFollowing.value = false; // Reset follow status initially

    try {
      // API endpoint: /api/profiles/<username>/
      const response = await axiosInstance.get<UserProfile>(`/profiles/${username}/`);
      currentProfile.value = response.data;
      console.log('ProfileStore: Profile data received:', currentProfile.value);

      // --- Set isFollowing state from API data ---
      // Ensure authStore is ready and it's not own profile before setting
      if (authStoreInstance.isAuthenticated && currentProfile.value?.username !== authStoreInstance.currentUser?.username) {
          // Check if the field exists in the response before assigning
          if (typeof response.data.is_followed_by_request_user === 'boolean') {
              isFollowing.value = response.data.is_followed_by_request_user;
              console.log(`ProfileStore: Initial follow status for ${username} set to: ${isFollowing.value}`);
          } else {
              console.warn(`ProfileStore: 'is_followed_by_request_user' field missing or not boolean in API response for ${username}. Defaulting follow status to false.`);
              isFollowing.value = false;
          }
      } else {
           isFollowing.value = false; // Can't follow self or if not logged in
           console.log(`ProfileStore: Setting follow status to false (own profile or not logged in)`);
      }
      // --- End setting state ---

    } catch (err: any) {
      console.error(`ProfileStore: Error fetching profile for ${username}:`, err);
      errorProfile.value = err.response?.data?.detail || err.message || 'Failed to fetch profile.';
      // Handle 404 specifically?
      if (err.response?.status === 404) {
           errorProfile.value = `Profile not found for user "${username}".`;
      }
      isFollowing.value = false; // Also reset on error
    } finally {
      isLoadingProfile.value = false;
    }
  }

  // --- REPLACE the old fetchUserPosts with THIS version ---
async function fetchUserPosts(username: string, page: number = 1) { // Add page parameter, default to 1
    console.log(`ProfileStore: Fetching posts for ${username}, page ${page}`);
    isLoadingPosts.value = true;
    errorPosts.value = null;
    // Clear posts only if fetching page 1
    if (page === 1) {
        userPosts.value = [];
        // Also reset part of pagination state when going back to page 1
        postsPagination.value.currentPage = 1;
        postsPagination.value.next = null;
        postsPagination.value.previous = null;
    }
  
    try {
      // Define interface for the expected API response structure HERE
      // (Moved from global scope for clarity, or keep global if preferred)
       interface PaginatedPostsResponse {
            count: number;
            next: string | null;
            previous: string | null;
            results: Post[];
       }
  
      // Pass page param to API call
      const response = await axiosInstance.get<PaginatedPostsResponse>(`/users/${username}/posts/`, {
          params: { page } // Send page as query parameter, e.g., /users/testuser1/posts/?page=2
      });
  
      // Assign posts for the current page
      userPosts.value = response.data.results;
  
      // --- Store pagination info from response ---
      postsPagination.value.count = response.data.count;
      postsPagination.value.next = response.data.next;
      postsPagination.value.previous = response.data.previous;
      postsPagination.value.currentPage = page; // Update current page
  
      // Calculate total pages (use a sensible default page size if results are empty)
      const pageSize = postsPagination.value.pageSize > 0 ? postsPagination.value.pageSize : 10; // Use stored/default size
      postsPagination.value.totalPages = Math.ceil(response.data.count / pageSize);
      // --- End storing pagination info ---
  
      console.log(`ProfileStore: Posts page ${page} received for ${username}:`, userPosts.value.length);
      console.log('ProfileStore: Updated pagination state:', postsPagination.value); // Log pagination state
  
    } catch (err: any) {
      console.error(`ProfileStore: Error fetching posts for ${username}, page ${page}:`, err);
      errorPosts.value = err.response?.data?.detail || err.message || 'Failed to fetch user posts.';
       if (err.response?.status === 404) {
           errorPosts.value = `Could not load posts for user "${username}".`;
       }
       // Clear posts and pagination on error
       userPosts.value = [];
       postsPagination.value = { count: 0, next: null, previous: null, currentPage: 1, totalPages: 1, pageSize: 10 };
    } finally {
      isLoadingPosts.value = false;
    }
  }
  // --- End of UPDATED fetchUserPosts function ---

  // --- ADD THIS FUNCTION ---
async function followUser(usernameToFollow: string) {
    // Check loading state and auth
    if (isLoadingFollow.value || !authStoreInstance.isAuthenticated) return;
    console.log(`ProfileStore: Attempting to follow ${usernameToFollow}`);
    isLoadingFollow.value = true; // Set loading
    try {
        // API call: POST /users/<username>/follow/
        await axiosInstance.post(`/users/${usernameToFollow}/follow/`);
        isFollowing.value = true; // Update state on success
        console.log(`ProfileStore: Successfully followed ${usernameToFollow}`);
    } catch (err: any) {
         console.error(`Error following ${usernameToFollow}:`, err);
         // Optional: Revert state on error if needed, but maybe not if API failed?
         // isFollowing.value = false;
    } finally {
        isLoadingFollow.value = false; // Unset loading
    }
}
// --- END ADD FUNCTION ---

  // --- ADD THIS FUNCTION ---
async function unfollowUser(usernameToUnfollow: string) {
    // Check loading state and auth
    if (isLoadingFollow.value || !authStoreInstance.isAuthenticated) return;
    console.log(`ProfileStore: Attempting to unfollow ${usernameToUnfollow}`);
    isLoadingFollow.value = true; // Set loading
    try {
        // API call: DELETE /users/<username>/follow/
        await axiosInstance.delete(`/users/${usernameToUnfollow}/follow/`);
        isFollowing.value = false; // Update state on success
        console.log(`ProfileStore: Successfully unfollowed ${usernameToUnfollow}`);
    } catch (err: any) {
         console.error(`Error unfollowing ${usernameToUnfollow}:`, err);
         // Optional: Revert state on error?
         // isFollowing.value = true;
    } finally {
        isLoadingFollow.value = false; // Unset loading
    }
}
// --- END ADD FUNCTION ---

  // Action to clear profile data when leaving the view
  // --- REPLACE the old clearProfileData with THIS version ---
function clearProfileData() {
    console.log('ProfileStore: Clearing profile data');
    currentProfile.value = null;
    userPosts.value = [];
    errorProfile.value = null;
    errorPosts.value = null;
    // --- ADD Resetting pagination state ---
    postsPagination.value = {
        count: 0,
        next: null,
        previous: null,
        currentPage: 1,
        totalPages: 1,
        pageSize: 10 // Reset to default
    };
    // --- END Resetting pagination state ---

     // --- ADD THESE TWO LINES ---
    isFollowing.value = false; // Reset follow status
    isLoadingFollow.value = false; // Reset follow loading status
    // --- END ADD ---
}
// --- End of UPDATED clearProfileData function ---


  // --- Return state and actions ---
  return {
    // --- Existing state ---
    currentProfile: currentProfile,
    userPosts: userPosts,
    isLoadingProfile: isLoadingProfile,
    isLoadingPosts: isLoadingPosts,
    errorProfile: errorProfile,
    errorPosts: errorPosts,
    postsPagination: postsPagination,
    // --- Added follow state ---
    isFollowing: isFollowing,
    isLoadingFollow: isLoadingFollow,
    // --- Existing actions ---
    fetchProfile: fetchProfile,
    fetchUserPosts: fetchUserPosts,
    clearProfileData: clearProfileData,
    // --- Added follow actions ---
    followUser: followUser,
    unfollowUser: unfollowUser,
  };
});