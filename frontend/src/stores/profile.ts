// C:\Users\Vinay\Project\frontend\src\stores\profile.ts
import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import { useAuthStore, type User } from '@/stores/auth'
import { usePostsStore, type Post, type PostAuthor } from '@/stores/posts'

export type ProfileUpdatePayload = {
  bio?: string
  headline?: string // ADDED
  location_city?: string
  location_state?: string
  skills?: string[]
  interests?: string[]
}

export interface UserProfile {
  user: User
  bio: string | null
  headline: string | null // ADDED
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

export interface RelationshipStatus {
  follow_status: 'not_following' | 'following' | 'followed_by' | 'self'
  connection_status: 'not_connected' | 'request_sent' | 'request_received' | 'connected' | 'self'
}

export const useProfileStore = defineStore('profile', () => {
  const authStore = useAuthStore()
  const postsStore = usePostsStore()

  const currentProfile = ref<UserProfile | null>(null)
  const postIdsByUsername = ref<{ [username: string]: number[] }>({})
  const nextPageUrlByUsername = ref<{ [username: string]: string | null }>({})
  const profilesByUsername = ref<{ [username: string]: UserProfile }>({})
  const hasFetchedPostsByUsername = ref<{ [username: string]: boolean }>({})
  const isLoadingProfile = ref(false)
  const isLoadingPosts = ref(false)
  const errorProfile = ref<string | null>(null)
  const errorPosts = ref<string | null>(null)
  const isFollowing = ref(false) // DEPRECATED but kept for now to avoid breaking other parts
  const isLoadingFollow = ref(false)
  const relationshipStatus = ref<RelationshipStatus | null>(null)

  function handlePostDeletedSignal(postId: number) {
    for (const username in postIdsByUsername.value) {
      postIdsByUsername.value[username] = postIdsByUsername.value[username].filter(
        (id) => id !== postId,
      )
    }
  }

  async function fetchProfile(username: string) {
    if (profilesByUsername.value[username]) {
      currentProfile.value = profilesByUsername.value[username]
      return
    }
    isLoadingProfile.value = true
    errorProfile.value = null
    try {
      const response = await axiosInstance.get<UserProfile>(`/profiles/${username}/`)
      const profile = response.data
      profilesByUsername.value[username] = profile
      currentProfile.value = profile
    } catch (err: any) {
      errorProfile.value = err.response?.data?.detail || `Profile not found for user "${username}".`
    } finally {
      isLoadingProfile.value = false
    }
  }

  async function fetchUserPosts(username: string, url: string | null = null) {
    if (!url && hasFetchedPostsByUsername.value[username]) return
    if (isLoadingPosts.value) return
    isLoadingPosts.value = true
    errorPosts.value = null
    const apiUrl = url || `/users/${username}/posts/`
    try {
      const response = await axiosInstance.get<PaginatedPostsResponse>(apiUrl)
      postsStore.addOrUpdatePosts(response.data.results)
      const newIds = response.data.results.map((post) => post.id)
      if (url) {
        postIdsByUsername.value[username] = [
          ...(postIdsByUsername.value[username] || []),
          ...newIds,
        ]
      } else {
        postIdsByUsername.value[username] = newIds
      }
      nextPageUrlByUsername.value[username] = response.data.next
      if (!url) hasFetchedPostsByUsername.value[username] = true
    } catch (err: any) {
      errorPosts.value = err.response?.data?.detail || 'Failed to fetch user posts.'
    } finally {
      isLoadingPosts.value = false
    }
  }

  async function refreshUserPosts(username: string) {
    const isInitialLoad = !hasFetchedPostsByUsername.value[username]
    if (isInitialLoad) isLoadingPosts.value = true
    errorPosts.value = null
    const apiUrl = `/users/${username}/posts/`
    try {
      const response = await axiosInstance.get<PaginatedPostsResponse>(apiUrl)
      const freshPosts = response.data.results
      postsStore.addOrUpdatePosts(freshPosts)
      postIdsByUsername.value[username] = freshPosts.map((p) => p.id)
      nextPageUrlByUsername.value[username] = response.data.next
      hasFetchedPostsByUsername.value[username] = true
    } catch (err: any) {
      errorPosts.value = err.response?.data?.detail || 'Failed to refresh user posts.'
    } finally {
      if (isInitialLoad) isLoadingPosts.value = false
    }
  }

  function addPostToProfileFeed(post: Post) {
    const username = post.author.username
    if (postIdsByUsername.value[username]) {
      postIdsByUsername.value[username].unshift(post.id)
    }
  }

  async function updateProfilePicture(username: string, pictureFile: File) {
    const formData = new FormData()
    formData.append('picture', pictureFile)
    try {
      const response = await axiosInstance.patch<UserProfile>(`/profiles/${username}/`, formData)
      const updatedProfile = response.data
      profilesByUsername.value[username] = updatedProfile
      if (currentProfile.value?.user.username === username) {
        currentProfile.value = updatedProfile
      }
      if (authStore.currentUser?.username === username) {
        authStore.updateCurrentUserPicture(updatedProfile.picture!)
      }
      const authorUpdates: Partial<PostAuthor> = { picture: updatedProfile.picture }
      const allPosts = Object.values(postsStore.posts)
      const postsToUpdate = allPosts.filter((p) => p.author.id === updatedProfile.user.id)
      const partialPostsToUpdate = postsToUpdate.map((p) => ({
        id: p.id,
        author: { ...p.author, ...authorUpdates },
      }))
      postsStore.addOrUpdatePosts(partialPostsToUpdate)
      return updatedProfile
    } catch (err: any) {
      throw new Error(
        err.response?.data?.picture?.join(' ') ||
          err.response?.data?.detail ||
          'Failed to update picture.',
      )
    }
  }

  async function followUser(usernameToFollow: string) {
    if (isLoadingFollow.value) return
    isLoadingFollow.value = true
    try {
      await axiosInstance.post(`/users/${usernameToFollow}/follow/`)
      await fetchRelationshipStatus(usernameToFollow)
    } finally {
      isLoadingFollow.value = false
    }
  }

  async function unfollowUser(usernameToUnfollow: string) {
    if (isLoadingFollow.value) return
    isLoadingFollow.value = true
    try {
      await axiosInstance.delete(`/users/${usernameToUnfollow}/follow/`)
      await fetchRelationshipStatus(usernameToUnfollow)
    } finally {
      isLoadingFollow.value = false
    }
  }

  async function fetchRelationshipStatus(username: string) {
    try {
      const response = await axiosInstance.get<RelationshipStatus>(
        `/users/${username}/relationship/`,
      )
      relationshipStatus.value = response.data
    } catch (error) {
      console.error('Failed to fetch relationship status:', error)
      relationshipStatus.value = null
    }
  }

  async function sendConnectRequest(username: string) {
    if (!currentProfile.value) return
    try {
      const receiverId = currentProfile.value.user.id
      await axiosInstance.post('/connections/requests/', { receiver: receiverId })
      if (relationshipStatus.value) {
        relationshipStatus.value.connection_status = 'request_sent'
      }
    } catch (error: any) {
      console.error('Failed to send connection request:', error)
      alert(error.response?.data?.detail || 'Could not send request.')
    }
  }

  async function acceptConnectRequest(username: string) {
    try {
      await axiosInstance.post(`/users/${username}/accept-request/`)
      if (relationshipStatus.value) {
        relationshipStatus.value.connection_status = 'connected'
        relationshipStatus.value.follow_status = 'following'
      }
    } catch (error: any) {
      console.error('Failed to accept connection request:', error)
      alert(error.response?.data?.detail || 'Could not accept request.')
    }
  }

  async function updateProfile(username: string, payload: ProfileUpdatePayload) {
    try {
      const response = await axiosInstance.patch<UserProfile>(`/profiles/${username}/`, payload)
      const updatedProfile = response.data
      profilesByUsername.value[username] = updatedProfile
      if (currentProfile.value?.user.username === username) {
        currentProfile.value = updatedProfile
      }
    } catch (err: any) {
      console.error('Failed to update profile:', err)
      throw new Error(
        err.response?.data?.detail || 'An unexpected error occurred while updating the profile.',
      )
    }
  }

  async function removeProfilePicture(username: string) {
    try {
      const response = await axiosInstance.patch<UserProfile>(`/profiles/${username}/`, {
        picture: null,
      })
      const updatedProfile = response.data
      profilesByUsername.value[username] = updatedProfile
      if (currentProfile.value?.user.username === username) {
        currentProfile.value = updatedProfile
      }
      if (authStore.currentUser?.username === username) {
        authStore.updateCurrentUserPicture(null)
      }
      const authorUpdates: Partial<PostAuthor> = { picture: null }
      const allPosts = Object.values(postsStore.posts)
      const postsToUpdate = allPosts.filter((p) => p.author.id === updatedProfile.user.id)
      const partialPostsToUpdate = postsToUpdate.map((p) => ({
        id: p.id,
        author: { ...p.author, ...authorUpdates },
      }))
      postsStore.addOrUpdatePosts(partialPostsToUpdate)
    } catch (err: any) {
      console.error('Failed to remove profile picture:', err)
      throw new Error(
        err.response?.data?.detail || 'An unexpected error occurred while removing the picture.',
      )
    }
  }

  function $reset() {
    currentProfile.value = null
    postIdsByUsername.value = {}
    nextPageUrlByUsername.value = {}
    profilesByUsername.value = {}
    hasFetchedPostsByUsername.value = {}
    isLoadingProfile.value = false
    isLoadingPosts.value = false
    errorProfile.value = null
    errorPosts.value = null
    isFollowing.value = false
    isLoadingFollow.value = false
    relationshipStatus.value = null
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
    refreshUserPosts,
    fetchNextPageOfUserPosts: (username: string) =>
      fetchUserPosts(username, nextPageUrlByUsername.value[username]),
    updateProfilePicture,
    followUser,
    unfollowUser,
    addPostToProfileFeed,
    handlePostDeletedSignal,
    updateProfile,
    removeProfilePicture,
    $reset,
    relationshipStatus,
    fetchRelationshipStatus,
    sendConnectRequest,
    acceptConnectRequest,
  }
})
