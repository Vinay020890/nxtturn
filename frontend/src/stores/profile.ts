// src/stores/profile.ts
import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import type { Post } from '@/stores/feed';
import { useAuthStore, type User } from '@/stores/auth';

export interface UserProfile {
  user: User;
  bio: string | null;
  location_city: string | null;
  location_state: string | null;
  college_name: string | null;
  major: string | null;
  graduation_year: number | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  skills: string[];
  interests: string[];
  picture: string | null;
  updated_at: string;
  is_followed_by_request_user: boolean;
}

export const useProfileStore = defineStore('profile', () => {
  const authStoreInstance = useAuthStore();

  const currentProfile = ref<UserProfile | null>(null);
  const userPosts = ref<Post[]>([]);
  const isLoadingProfile = ref(false);
  const isLoadingPosts = ref(false);
  const errorProfile = ref<string | null>(null);
  const errorPosts = ref<string | null>(null);
  const postsPagination = ref({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    currentPage: 1,
    totalPages: 1,
    pageSize: 10
  });
  const isFollowing = ref(false);
  const isLoadingFollow = ref(false);

  async function fetchProfile(username: string) {
    console.log(`ProfileStore: Fetching profile for ${username}`);
    isLoadingProfile.value = true;
    errorProfile.value = null;
    // currentProfile.value = null; // Clear only if username changes, handled by watcher/clearProfileData
    isFollowing.value = false;

    try {
      const response = await axiosInstance.get<UserProfile>(`/profiles/${username}/`);
      currentProfile.value = response.data;
      console.log('ProfileStore: Profile data received:', currentProfile.value);

      if (authStoreInstance.isAuthenticated && currentProfile.value?.user?.username !== authStoreInstance.currentUser?.username) {
          if (typeof response.data.is_followed_by_request_user === 'boolean') {
              isFollowing.value = response.data.is_followed_by_request_user;
          } else {
              isFollowing.value = false;
          }
      } else {
           isFollowing.value = false;
      }
    } catch (err: any) {
      console.error(`ProfileStore: Error fetching profile for ${username}:`, err);
      errorProfile.value = err.response?.data?.detail || err.message || 'Failed to fetch profile.';
      if (err.response?.status === 404) {
           errorProfile.value = `Profile not found for user "${username}".`;
      }
      isFollowing.value = false;
    } finally {
      isLoadingProfile.value = false;
    }
  }

  async function fetchUserPosts(username: string, page: number = 1) {
    // ... (existing fetchUserPosts logic - keep as is) ...
    console.log(`ProfileStore: Fetching posts for ${username}, page ${page}`);
    isLoadingPosts.value = true;
    errorPosts.value = null;
    if (page === 1) {
        userPosts.value = [];
        postsPagination.value.currentPage = 1;
        postsPagination.value.next = null;
        postsPagination.value.previous = null;
    }
    try {
       interface PaginatedPostsResponse {
            count: number;
            next: string | null;
            previous: string | null;
            results: Post[];
       }
      const response = await axiosInstance.get<PaginatedPostsResponse>(`/users/${username}/posts/`, {
          params: { page }
      });
      userPosts.value = response.data.results;
      postsPagination.value.count = response.data.count;
      postsPagination.value.next = response.data.next;
      postsPagination.value.previous = response.data.previous;
      postsPagination.value.currentPage = page;
      const pageSize = postsPagination.value.pageSize > 0 ? postsPagination.value.pageSize : 10;
      postsPagination.value.totalPages = Math.ceil(response.data.count / pageSize);
    } catch (err: any) {
      console.error(`ProfileStore: Error fetching posts for ${username}, page ${page}:`, err);
      errorPosts.value = err.response?.data?.detail || err.message || 'Failed to fetch user posts.';
       if (err.response?.status === 404) {
           errorPosts.value = `Could not load posts for user "${username}".`;
       }
       userPosts.value = [];
       postsPagination.value = { count: 0, next: null, previous: null, currentPage: 1, totalPages: 1, pageSize: 10 };
    } finally {
      isLoadingPosts.value = false;
    }
  }

  async function followUser(usernameToFollow: string) {
    // ... (existing followUser logic - keep as is) ...
    if (isLoadingFollow.value || !authStoreInstance.isAuthenticated) return;
    isLoadingFollow.value = true;
    try {
        await axiosInstance.post(`/users/${usernameToFollow}/follow/`);
        isFollowing.value = true;
    } catch (err: any) { console.error(`Error following ${usernameToFollow}:`, err); }
    finally { isLoadingFollow.value = false; }
  }

  async function unfollowUser(usernameToUnfollow: string) {
    // ... (existing unfollowUser logic - keep as is) ...
    if (isLoadingFollow.value || !authStoreInstance.isAuthenticated) return;
    isLoadingFollow.value = true;
    try {
        await axiosInstance.delete(`/users/${usernameToUnfollow}/follow/`);
        isFollowing.value = false;
    } catch (err: any) { console.error(`Error unfollowing ${usernameToUnfollow}:`, err); }
    finally { isLoadingFollow.value = false; }
  }

  function clearProfileData() {
    // ... (existing clearProfileData logic - keep as is) ...
    currentProfile.value = null;
    userPosts.value = [];
    errorProfile.value = null;
    errorPosts.value = null;
    postsPagination.value = { count: 0, next: null, previous: null, currentPage: 1, totalPages: 1, pageSize: 10 };
    isFollowing.value = false;
    isLoadingFollow.value = false;
  }

  // --- ACTION TO UPDATE/UPLOAD PROFILE PICTURE ---
  async function updateProfilePicture(username: string, pictureFile: File) {
    console.log(`ProfileStore: Attempting to update picture for ${username}`);
    // Optional: You could add specific loading/error refs for this action if desired
    // e.g., const isUploadingPic = ref(false); const picUploadError = ref<string | null>(null);
    // For now, we can rely on the component to manage its own isUploadingPicture state.

    const formData = new FormData();
    formData.append('picture', pictureFile); // 'picture' must match the model field name

    try {
      const apiUrl = `/profiles/${username}/`;
      console.log(`ProfileStore: Calling API: PATCH ${apiUrl}`);

      const response = await axiosInstance.patch<UserProfile>(apiUrl, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data && response.data.picture) {
        console.log('ProfileStore: Picture updated successfully. New picture URL:', response.data.picture);
        currentProfile.value = response.data; // Update the store's profile data
        return response.data;
      } else {
        console.error('ProfileStore: Picture update API call succeeded but returned invalid data', response.data);
        throw new Error("Upload succeeded, but server response was unexpected.");
      }
    } catch (err: any) {
      console.error(`ProfileStore: Error updating picture for ${username}:`, err);
      let errorMessage = 'Failed to update profile picture.';
      if (err.response && err.response.data) {
          if (typeof err.response.data.picture === 'string') {
              errorMessage = err.response.data.picture;
          } else if (Array.isArray(err.response.data.picture)) {
              errorMessage = err.response.data.picture.join(' ');
          } else if (err.response.data.detail) {
              errorMessage = err.response.data.detail;
          } else if (typeof err.response.data === 'object') {
              const fieldErrors = Object.values(err.response.data).flat();
              if (fieldErrors.length > 0) {
                  errorMessage = fieldErrors.join(' ');
              }
          }
      } else if (err.message) {
          errorMessage = err.message;
      }
      throw new Error(errorMessage);
    } finally {
      console.log(`ProfileStore: Update picture attempt finished for ${username}.`);
    }
  }

  // ---- ADD THIS NEW ACTION ----
function toggleLikeInUserPosts(postId: number, postType: string) {
  // console.log(`ProfileStore: Attempting to toggle like in userPosts for Post ID: ${postId}, Type: ${postType}`);
  if (userPosts.value && userPosts.value.length > 0) {
    const postIndex = userPosts.value.findIndex(p => p.id === postId && p.post_type === postType);
    
    if (postIndex !== -1) {
      const post = userPosts.value[postIndex];
      // Toggle like status and update count locally
      post.is_liked_by_user = !post.is_liked_by_user;
      post.like_count += post.is_liked_by_user ? 1 : -1;
      
     // console.log(`ProfileStore: Toggled like for post ${postId} in userPosts. New liked state: ${post.is_liked_by_user}, New count: ${post.like_count}`);
    } else {
      console.warn(`ProfileStore: Post ${postId} (type ${postType}) not found in userPosts. Cannot toggle like state locally.`);
    }
  } else {
    console.warn(`ProfileStore: userPosts array is empty or not yet initialized. Cannot toggle like for Post ID: ${postId}`);
  }
}
// ---- END OF NEW ACTION ----
  // --- END ACTION ---
// ---- ADD THIS NEW ACTION ----
function incrementCommentCountInUserPosts(postId: number, postType: string) {
  console.log(`ProfileStore: Attempting to increment comment count in userPosts for Post ID: ${postId}, Type: ${postType}`);
  if (userPosts.value && userPosts.value.length > 0) {
    const postIndex = userPosts.value.findIndex(p => p.id === postId && p.post_type === postType);
    if (postIndex !== -1) {
      if (typeof userPosts.value[postIndex].comment_count === 'number') {
        userPosts.value[postIndex].comment_count!++;
      } else {
        userPosts.value[postIndex].comment_count = 1;
      }
      console.log(`ProfileStore: Incremented comment_count for post ${postId} in userPosts. New count: ${userPosts.value[postIndex].comment_count}`);
    } else {
      console.warn(`ProfileStore: Post ID ${postId} (Type: ${postType}) not found in userPosts. Cannot increment comment count.`);
    }
  } else {
    console.warn(`ProfileStore: userPosts array is empty or not initialized. Cannot increment for Post ID: ${postId}`);
  }
}
// ---- END OF NEW ACTION ----

  return {
    currentProfile,
    userPosts,
    isLoadingProfile,
    isLoadingPosts,
    errorProfile,
    errorPosts,
    postsPagination,
    isFollowing,
    isLoadingFollow,
    fetchProfile,
    fetchUserPosts,
    clearProfileData,
    followUser,
    unfollowUser,
    updateProfilePicture, // <-- Ensure this is returned
    toggleLikeInUserPosts,
    incrementCommentCountInUserPosts,
  };
});