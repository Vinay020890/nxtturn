// C:\Users\Vinay\Project\frontend\src\stores\profile.ts

import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import type { Post } from '@/stores/feed'
import { useAuthStore, type User } from '@/stores/auth'

export interface UserProfile {
  user: User
  bio: string | null
  location_city: string | null
  location_state: string | null
  college_name: string | null
  major: string | null
  graduation_year: number | null
  linkedin_url: string | null
  portfolio_url: string | null
  skills: string[]
  interests: string[]
  picture: string | null
  updated_at: string
  is_followed_by_request_user: boolean
}

// --- NEW INTERFACE FOR THE API RESPONSE ---
interface PaginatedPostsResponse {
  count: number
  next: string | null
  previous: string | null
  results: Post[]
}

export const useProfileStore = defineStore('profile', () => {
  const authStoreInstance = useAuthStore()

  const currentProfile = ref<UserProfile | null>(null)
  const userPosts = ref<Post[]>([])
  const isLoadingProfile = ref(false)
  const isLoadingPosts = ref(false)
  const errorProfile = ref<string | null>(null)
  const errorPosts = ref<string | null>(null)

  // --- SIMPLIFIED PAGINATION STATE ---
  // We only need to know the URL for the next page
  const userPostsNextPageUrl = ref<string | null>(null)

  const isFollowing = ref(false)
  const isLoadingFollow = ref(false)

  async function fetchProfile(username: string) {
    isLoadingProfile.value = true
    errorProfile.value = null
    isFollowing.value = false
    try {
      const response = await axiosInstance.get<UserProfile>(`/profiles/${username}/`)
      currentProfile.value = response.data
      if (
        authStoreInstance.isAuthenticated &&
        currentProfile.value?.user?.username !== authStoreInstance.currentUser?.username
      ) {
        isFollowing.value = response.data.is_followed_by_request_user
      }
    } catch (err: any) {
      errorProfile.value = err.response?.data?.detail || `Profile not found for user "${username}".`
    } finally {
      isLoadingProfile.value = false
    }
  }

  // --- REFACTORED fetchUserPosts TO SUPPORT APPENDING ---
  async function fetchUserPosts(username: string, url: string | null = null) {
    if (isLoadingPosts.value) return // Prevent duplicate calls
    isLoadingPosts.value = true
    errorPosts.value = null

    // Use the provided URL, or construct the initial one
    const apiUrl = url || `/users/${username}/posts/`

    try {
      const response = await axiosInstance.get<PaginatedPostsResponse>(apiUrl)
      const fetchedPosts = response.data.results.map((post) => ({
        ...post,
        isLiking: false,
        isDeleting: false,
        isUpdating: false,
      }))

      if (url) {
        // If a URL was provided, it's a "load more" call, so append the posts
        userPosts.value.push(...fetchedPosts)
      } else {
        // If no URL, it's the first call, so replace the posts
        userPosts.value = fetchedPosts
      }

      // Update the next page URL
      userPostsNextPageUrl.value = response.data.next
    } catch (err: any) {
      errorPosts.value = err.response?.data?.detail || 'Failed to fetch user posts.'
    } finally {
      isLoadingPosts.value = false
    }
  }

  // --- NEW ACTION FOR CONVENIENCE, JUST LIKE IN feed.ts ---
  async function fetchNextPageOfUserPosts(username: string) {
    if (userPostsNextPageUrl.value && !isLoadingPosts.value) {
      await fetchUserPosts(username, userPostsNextPageUrl.value)
    }
  }

  async function followUser(usernameToFollow: string) {
    if (isLoadingFollow.value || !authStoreInstance.isAuthenticated) return
    isLoadingFollow.value = true
    try {
      await axiosInstance.post(`/users/${usernameToFollow}/follow/`)
      isFollowing.value = true
    } catch (err: any) {
      console.error(`Error following ${usernameToFollow}:`, err)
    } finally {
      isLoadingFollow.value = false
    }
  }

  async function unfollowUser(usernameToUnfollow: string) {
    if (isLoadingFollow.value || !authStoreInstance.isAuthenticated) return
    isLoadingFollow.value = true
    try {
      await axiosInstance.delete(`/users/${usernameToUnfollow}/follow/`)
      isFollowing.value = false
    } catch (err: any) {
      console.error(`Error unfollowing ${usernameToUnfollow}:`, err)
    } finally {
      isLoadingFollow.value = false
    }
  }

  function clearProfileData() {
    currentProfile.value = null
    userPosts.value = []
    errorProfile.value = null
    errorPosts.value = null
    userPostsNextPageUrl.value = null // Reset the next page URL
    isFollowing.value = false
  }

  async function updateProfilePicture(username: string, pictureFile: File) {
    const formData = new FormData()
    formData.append('picture', pictureFile)
    try {
      const response = await axiosInstance.patch<UserProfile>(`/profiles/${username}/`, formData)
      currentProfile.value = response.data
      if (
        authStoreInstance.currentUser &&
        authStoreInstance.currentUser.username === username &&
        response.data.picture
      ) {
        // If it is, call the new action in the auth store to synchronize the state.
        authStoreInstance.updateCurrentUserPicture(response.data.picture)
      }
      return response.data
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.picture?.join(' ') ||
        err.response?.data?.detail ||
        'Failed to update profile picture.'
      throw new Error(errorMessage)
    }
  }

  return {
    // State
    currentProfile,
    userPosts,
    isLoadingProfile,
    isLoadingPosts,
    errorProfile,
    errorPosts,
    userPostsNextPageUrl, // EXPORT the new next page URL state
    isFollowing,
    isLoadingFollow,
    // Actions
    fetchProfile,
    fetchUserPosts,
    fetchNextPageOfUserPosts, // EXPORT the new action
    clearProfileData,
    followUser,
    unfollowUser,
    updateProfilePicture,
  }
})
