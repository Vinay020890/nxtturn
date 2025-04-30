// src/stores/profile.ts
import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import type { Post } from '@/stores/feed'; // Import Post type for user posts

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
  // --- State ---
  const currentProfile = ref<UserProfile | null>(null);
  const userPosts = ref<Post[]>([]);
  const isLoadingProfile = ref(false);
  const isLoadingPosts = ref(false);
  const errorProfile = ref<string | null>(null);
  const errorPosts = ref<string | null>(null);

  // --- Actions ---

  // Action to fetch profile details
  async function fetchProfile(username: string) {
    console.log(`ProfileStore: Fetching profile for ${username}`);
    isLoadingProfile.value = true;
    errorProfile.value = null;
    currentProfile.value = null; // Clear previous profile

    try {
      // API endpoint: /api/profiles/<username>/
      const response = await axiosInstance.get<UserProfile>(`/profiles/${username}/`);
      currentProfile.value = response.data;
      console.log('ProfileStore: Profile data received:', currentProfile.value);
    } catch (err: any) {
      console.error(`ProfileStore: Error fetching profile for ${username}:`, err);
      errorProfile.value = err.response?.data?.detail || err.message || 'Failed to fetch profile.';
       // Handle 404 specifically?
       if (err.response?.status === 404) {
           errorProfile.value = `Profile not found for user "${username}".`;
       }
    } finally {
      isLoadingProfile.value = false;
    }
  }

  // Action to fetch posts by a specific user
  async function fetchUserPosts(username: string) {
    console.log(`ProfileStore: Fetching posts for ${username}`);
    isLoadingPosts.value = true;
    errorPosts.value = null;
    userPosts.value = []; // Clear previous posts

    try {
      // API endpoint: /api/users/<username>/posts/
      // Assuming this endpoint returns a paginated response like the feed
      // We might need to handle pagination later
      // For now, fetch first page? Or modify backend to return all? Let's assume paginated for now.
      const response = await axiosInstance.get<{ results: Post[] }>(`/users/${username}/posts/`); // Adjust if not paginated
      userPosts.value = response.data.results; // Assuming paginated structure
      console.log(`ProfileStore: Posts received for ${username}:`, userPosts.value.length);
    } catch (err: any) {
      console.error(`ProfileStore: Error fetching posts for ${username}:`, err);
      errorPosts.value = err.response?.data?.detail || err.message || 'Failed to fetch user posts.';
       if (err.response?.status === 404) {
           // This might happen if the user exists but has no posts, or if the user doesn't exist
           // Distinguish based on fetchProfile result? Or just show "No posts found".
           errorPosts.value = `Could not load posts for user "${username}".`;
       }
    } finally {
      isLoadingPosts.value = false;
    }
  }

  // Action to clear profile data when leaving the view
  function clearProfileData() {
      console.log('ProfileStore: Clearing profile data');
      currentProfile.value = null;
      userPosts.value = [];
      errorProfile.value = null;
      errorPosts.value = null;
      // Reset pagination state too if added
  }


  // --- Return state and actions ---
  return {
    currentProfile,
    userPosts,
    isLoadingProfile,
    isLoadingPosts,
    errorProfile,
    errorPosts,
    fetchProfile,
    fetchUserPosts,
    clearProfileData,
  };
});