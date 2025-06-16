// src/stores/profile.ts
import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';

// --- IMPORTANT: Import the updated Post interface AND the new PostMedia interface ---
import type { Post, PostMedia } from '@/stores/feed'; 
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
  const userPosts = ref<Post[]>([]); // This now uses the updated Post interface automatically
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

  // No changes needed to the functions below this line for the media gallery feature.
  // They already use the 'Post' type which we've updated centrally in feed.ts.

  async function fetchProfile(username: string) {
    isLoadingProfile.value = true;
    errorProfile.value = null;
    isFollowing.value = false;
    try {
      const response = await axiosInstance.get<UserProfile>(`/profiles/${username}/`);
      currentProfile.value = response.data;
      if (authStoreInstance.isAuthenticated && currentProfile.value?.user?.username !== authStoreInstance.currentUser?.username) {
        isFollowing.value = response.data.is_followed_by_request_user;
      }
    } catch (err: any) {
      errorProfile.value = err.response?.data?.detail || `Profile not found for user "${username}".`;
    } finally {
      isLoadingProfile.value = false;
    }
  }

  async function fetchUserPosts(username: string, page: number = 1) {
    isLoadingPosts.value = true;
    errorPosts.value = null;
    if (page === 1) {
        userPosts.value = [];
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
      postsPagination.value.totalPages = Math.ceil(response.data.count / postsPagination.value.pageSize);
    } catch (err: any) {
      errorPosts.value = err.response?.data?.detail || 'Failed to fetch user posts.';
    } finally {
      isLoadingPosts.value = false;
    }
  }

  async function followUser(usernameToFollow: string) {
    if (isLoadingFollow.value || !authStoreInstance.isAuthenticated) return;
    isLoadingFollow.value = true;
    try {
        await axiosInstance.post(`/users/${usernameToFollow}/follow/`);
        isFollowing.value = true;
    } catch (err: any) { console.error(`Error following ${usernameToFollow}:`, err); }
    finally { isLoadingFollow.value = false; }
  }

  async function unfollowUser(usernameToUnfollow: string) {
    if (isLoadingFollow.value || !authStoreInstance.isAuthenticated) return;
    isLoadingFollow.value = true;
    try {
        await axiosInstance.delete(`/users/${usernameToUnfollow}/follow/`);
        isFollowing.value = false;
    } catch (err: any) { console.error(`Error unfollowing ${usernameToUnfollow}:`, err); }
    finally { isLoadingFollow.value = false; }
  }

  function clearProfileData() {
    currentProfile.value = null;
    userPosts.value = [];
    errorProfile.value = null;
    errorPosts.value = null;
    postsPagination.value = { count: 0, next: null, previous: null, currentPage: 1, totalPages: 1, pageSize: 10 };
    isFollowing.value = false;
  }

  async function updateProfilePicture(username: string, pictureFile: File) {
    const formData = new FormData();
    formData.append('picture', pictureFile);
    try {
      const response = await axiosInstance.patch<UserProfile>(`/profiles/${username}/`, formData);
      currentProfile.value = response.data;
      return response.data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.picture?.join(' ') || err.response?.data?.detail || 'Failed to update profile picture.';
      throw new Error(errorMessage);
    }
  }

  function toggleLikeInUserPosts(postId: number, postType: string) {
    const postIndex = userPosts.value.findIndex(p => p.id === postId && p.post_type === postType);
    if (postIndex !== -1) {
      const post = userPosts.value[postIndex];
      post.is_liked_by_user = !post.is_liked_by_user;
      post.like_count += post.is_liked_by_user ? 1 : -1;
    }
  }

  function incrementCommentCountInUserPosts(postId: number, postType: string) {
    const postIndex = userPosts.value.findIndex(p => p.id === postId && p.post_type === postType);
    if (postIndex !== -1) {
      userPosts.value[postIndex].comment_count = (userPosts.value[postIndex].comment_count || 0) + 1;
    }
  }

  function updateUserPost(updatedPostData: Post) {
    const postIndex = userPosts.value.findIndex(p => p.id === updatedPostData.id && p.post_type === updatedPostData.post_type);
    if (postIndex !== -1) {
      userPosts.value[postIndex] = { 
          ...userPosts.value[postIndex],
          ...updatedPostData,
          isUpdating: false
      };
    }
  }

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
    updateProfilePicture,
    toggleLikeInUserPosts,
    incrementCommentCountInUserPosts,
    updateUserPost,
  };
});