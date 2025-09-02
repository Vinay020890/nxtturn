// C:\Users\Vinay\Project\frontend\src\stores\profile.ts

import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import { useFeedStore, type Post } from '@/stores/feed' // <-- IMPORT useFeedStore
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

  async function fetchUserPosts(username: string, url: string | null = null) {
    if (isLoadingPosts.value) return
    isLoadingPosts.value = true
    errorPosts.value = null

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
        userPosts.value.push(...fetchedPosts)
      } else {
        userPosts.value = fetchedPosts
      }
      userPostsNextPageUrl.value = response.data.next
    } catch (err: any) {
      errorPosts.value = err.response?.data?.detail || 'Failed to fetch user posts.'
    } finally {
      isLoadingPosts.value = false
    }
  }

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

  function $reset() {
    currentProfile.value = null
    userPosts.value = []
    errorProfile.value = null
    errorPosts.value = null
    userPostsNextPageUrl.value = null
    isFollowing.value = false
  }

  // --- THIS FUNCTION IS MODIFIED ---
  async function updateProfilePicture(username: string, pictureFile: File) {
    const formData = new FormData()
    formData.append('picture', pictureFile)
    try {
      const response = await axiosInstance.patch<UserProfile>(`/profiles/${username}/`, formData)
      const updatedProfile = response.data
      currentProfile.value = updatedProfile

      if (
        authStoreInstance.currentUser &&
        authStoreInstance.currentUser.username === username &&
        updatedProfile.picture
      ) {
        authStoreInstance.updateCurrentUserPicture(updatedProfile.picture)
      }

      // --- THIS IS THE FIX ---
      // Get an instance of the feed store
      const feedStore = useFeedStore()

      // Tell the feed store to update the author's picture in all cached posts
      if (authStoreInstance.currentUser) {
        feedStore.updateAuthorDetailsInAllPosts(authStoreInstance.currentUser.id, {
          picture: updatedProfile.picture,
        })
      }
      // --- END OF FIX ---

      return updatedProfile
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.picture?.join(' ') ||
        err.response?.data?.detail ||
        'Failed to update profile picture.'
      throw new Error(errorMessage)
    }
  }

  function addPostToProfileFeed(post: Post) {
    if (currentProfile.value?.user.id === post.author.id) {
      userPosts.value.unshift(post)
    }
  }

  return {
    currentProfile,
    userPosts,
    isLoadingProfile,
    isLoadingPosts,
    errorProfile,
    errorPosts,
    userPostsNextPageUrl,
    isFollowing,
    isLoadingFollow,
    fetchProfile,
    fetchUserPosts,
    fetchNextPageOfUserPosts,
    $reset,
    followUser,
    unfollowUser,
    updateProfilePicture,
    addPostToProfileFeed
  }
})
