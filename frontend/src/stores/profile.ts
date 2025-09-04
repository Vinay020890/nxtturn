// C:\Users\Vinay\Project\frontend\src\stores\profile.ts
// FINAL HYBRID FIX
import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import { useAuthStore, type User } from '@/stores/auth';
import { usePostsStore, type Post, type PostAuthor } from '@/stores/posts';

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
interface PaginatedPostsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Post[];
}

export const useProfileStore = defineStore('profile', () => {
  const authStore = useAuthStore();
  const postsStore = usePostsStore();

  const currentProfile = ref<UserProfile | null>(null);
  const postIdsByUsername = ref<{ [username: string]: number[] }>({});
  const nextPageUrlByUsername = ref<{ [username: string]: string | null }>({});
  const profilesByUsername = ref<{ [username: string]: UserProfile }>({});
  const hasFetchedPostsByUsername = ref<{ [username: string]: boolean }>({});
  const isLoadingProfile = ref(false);
  const isLoadingPosts = ref(false);
  const errorProfile = ref<string | null>(null);
  const errorPosts = ref<string | null>(null);
  const isFollowing = ref(false);
  const isLoadingFollow = ref(false);

  async function fetchProfile(username: string) {
    if (profilesByUsername.value[username]) {
      currentProfile.value = profilesByUsername.value[username];
      isFollowing.value = currentProfile.value.is_followed_by_request_user;
      return;
    }
    isLoadingProfile.value = true;
    errorProfile.value = null;
    try {
      const response = await axiosInstance.get<UserProfile>(`/profiles/${username}/`);
      const profile = response.data;
      profilesByUsername.value[username] = profile;
      currentProfile.value = profile;
      isFollowing.value = profile.is_followed_by_request_user;
    } catch (err: any) {
      errorProfile.value = err.response?.data?.detail || `Profile not found for user "${username}".`;
    } finally {
      isLoadingProfile.value = false;
    }
  }

  async function fetchUserPosts(username: string, url: string | null = null) {
    if (!url && hasFetchedPostsByUsername.value[username]) return;
    if (isLoadingPosts.value) return;
    isLoadingPosts.value = true;
    errorPosts.value = null;
    const apiUrl = url || `/users/${username}/posts/`;
    try {
      const response = await axiosInstance.get<PaginatedPostsResponse>(apiUrl);
      postsStore.addOrUpdatePosts(response.data.results);
      const newIds = response.data.results.map((post) => post.id);
      if (url) {
        postIdsByUsername.value[username] = [...(postIdsByUsername.value[username] || []), ...newIds];
      } else {
        postIdsByUsername.value[username] = newIds;
      }
      nextPageUrlByUsername.value[username] = response.data.next;
      if(!url) hasFetchedPostsByUsername.value[username] = true;
    } catch (err: any) {
      errorPosts.value = err.response?.data?.detail || 'Failed to fetch user posts.';
    } finally {
      isLoadingPosts.value = false;
    }
  }
  
  // [HYBRID FIX] NEW ACTION FOR BACKGROUND RE-VALIDATION
  async function refreshUserPosts(username: string) {
    const isInitialLoad = !hasFetchedPostsByUsername.value[username];
    // Only show a full loader on the very first visit to this profile
    if (isInitialLoad) isLoadingPosts.value = true;
    errorPosts.value = null;
    const apiUrl = `/users/${username}/posts/`;
    try {
      const response = await axiosInstance.get<PaginatedPostsResponse>(apiUrl);
      const freshPosts = response.data.results;
      postsStore.addOrUpdatePosts(freshPosts);
      // Replace the old list of IDs with the fresh one from the server
      postIdsByUsername.value[username] = freshPosts.map(p => p.id);
      nextPageUrlByUsername.value[username] = response.data.next;
      hasFetchedPostsByUsername.value[username] = true;
    } catch (err: any) {
      errorPosts.value = err.response?.data?.detail || 'Failed to refresh user posts.';
    } finally {
      if (isInitialLoad) isLoadingPosts.value = false;
    }
  }
  
  function addPostToProfileFeed(post: Post) {
    const username = post.author.username;
    if (postIdsByUsername.value[username]) {
      postIdsByUsername.value[username].unshift(post.id);
    }
  }
  
  async function updateProfilePicture(username: string, pictureFile: File) {
    const formData = new FormData();
    formData.append('picture', pictureFile);
    try {
      const response = await axiosInstance.patch<UserProfile>(`/profiles/${username}/`, formData);
      const updatedProfile = response.data;
      profilesByUsername.value[username] = updatedProfile;
      if (currentProfile.value?.user.username === username) {
        currentProfile.value = updatedProfile;
      }
      if (authStore.currentUser?.username === username) {
        authStore.updateCurrentUserPicture(updatedProfile.picture!);
      }
      const authorUpdates: Partial<PostAuthor> = { picture: updatedProfile.picture };
      const allPosts = Object.values(postsStore.posts);
      const postsToUpdate = allPosts.filter(p => p.author.id === updatedProfile.user.id);
      const partialPostsToUpdate = postsToUpdate.map(p => ({
          id: p.id,
          author: { ...p.author, ...authorUpdates }
      }));
      postsStore.addOrUpdatePosts(partialPostsToUpdate);
      return updatedProfile;
    } catch (err: any) {
      throw new Error(err.response?.data?.picture?.join(' ') || err.response?.data?.detail || 'Failed to update picture.');
    }
  }

  async function followUser(usernameToFollow: string) {
    if (isLoadingFollow.value) return;
    isLoadingFollow.value = true;
    try {
        await axiosInstance.post(`/users/${usernameToFollow}/follow/`);
        if (currentProfile.value) currentProfile.value.is_followed_by_request_user = true;
        isFollowing.value = true;
    } finally {
        isLoadingFollow.value = false;
    }
  }

  async function unfollowUser(usernameToUnfollow: string) {
    if (isLoadingFollow.value) return;
    isLoadingFollow.value = true;
    try {
        await axiosInstance.delete(`/users/${usernameToUnfollow}/follow/`);
        if (currentProfile.value) currentProfile.value.is_followed_by_request_user = false;
        isFollowing.value = false;
    } finally {
        isLoadingFollow.value = false;
    }
  }
  
  function $reset() {
    currentProfile.value = null;
    postIdsByUsername.value = {};
    nextPageUrlByUsername.value = {};
    profilesByUsername.value = {};
    hasFetchedPostsByUsername.value = {};
    isLoadingProfile.value = false;
    isLoadingPosts.value = false;
    errorProfile.value = null;
    errorPosts.value = null;
    isFollowing.value = false;
    isLoadingFollow.value = false;
  }

  return {
    currentProfile,
    postIdsByUsername,
    nextPageUrlByUsername,
    isLoadingProfile,
    isLoadingPosts,
    errorProfile,
    errorPosts,
    isFollowing,
    isLoadingFollow,
    fetchProfile,
    fetchUserPosts,
    refreshUserPosts, // [HYBRID FIX] Expose the new action
    fetchNextPageOfUserPosts: (username: string) => fetchUserPosts(username, nextPageUrlByUsername.value[username]),
    updateProfilePicture,
    followUser,
    unfollowUser,
    addPostToProfileFeed,
    $reset
  }
});