// C:\Users\Vinay\Project\frontend\src\stores\group.ts

import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import type { User } from './auth'
import type { Post } from './feed'
import { useAuthStore } from './auth'

// --- Interface Definitions ---

export interface Group {
  id: number
  slug: string
  name: string
  description: string
  creator: User
  members: User[]
  member_count: number
  is_member: boolean
  is_creator?: boolean // ADDITION: Add the optional is_creator flag from the API
  created_at: string
  privacy_level: 'public' | 'private'
}

interface PaginatedGroupResponse {
  count: number
  next: string | null
  previous: string | null
  results: Group[]
}

interface CursorPaginatedGroupPostResponse {
  next: string | null
  previous: string | null
  results: Post[]
}

// --- Store Definition ---

export const useGroupStore = defineStore('group', () => {
  // --- State ---
  const currentGroup = ref<Group | null>(null)
  const groupPosts = ref<Post[]>([])
  const isLoadingGroup = ref(false)
  const groupError = ref<string | null>(null)
  const isJoiningLeaving = ref(false)
  const joinLeaveError = ref<string | null>(null)

  const isLoadingGroupPosts = ref(false)
  const groupPostsNextCursor = ref<string | null>(null)

  const allGroups = ref<Group[]>([])
  const isLoadingAllGroups = ref(false)
  const allGroupsError = ref<string | null>(null)
  const allGroupsNextPageUrl = ref<string | null>(null)
  const allGroupsHasNextPage = ref(false)

  const isCreatingGroup = ref(false)
  const createGroupError = ref<string | object | null>(null)

  // --- ADDITION: NEW STATE FOR DELETION ---
  const isDeletingGroup = ref(false)
  const deleteGroupError = ref<string | null>(null)

  const isTransferringOwnership = ref(false)
  const transferOwnershipError = ref<string | null>(null)

  const groupSearchResults = ref<Group[]>([])
  const isLoadingGroupSearch = ref(false)
  const groupSearchError = ref<string | null>(null)

  function $reset() {
    currentGroup.value = null
    groupPosts.value = []
    isLoadingGroup.value = false
    groupError.value = null
    isJoiningLeaving.value = false
    joinLeaveError.value = null
    isLoadingGroupPosts.value = false
    groupPostsNextCursor.value = null

    allGroups.value = []
    isLoadingAllGroups.value = false
    allGroupsError.value = null
    allGroupsNextPageUrl.value = null
    allGroupsHasNextPage.value = false

    isCreatingGroup.value = false
    createGroupError.value = null

    // ADDITION: Reset new state
    isDeletingGroup.value = false
    deleteGroupError.value = null
  }

  // --- Targeted Reset Functions ---
  function resetGroupFeedState() {
    currentGroup.value = null
    groupPosts.value = []
    groupPostsNextCursor.value = null
    isLoadingGroupPosts.value = false
    groupError.value = null
    console.log('Individual group feed state has been reset.')
  }

  function resetAllGroupsState() {
    allGroups.value = []
    allGroupsNextPageUrl.value = null
    allGroupsHasNextPage.value = false
    isLoadingAllGroups.value = false
    allGroupsError.value = null
    console.log('"All Groups" discovery state has been reset.')
  }

  // --- Actions ---
  async function searchGroups(query: string) {
    if (!query.trim()) {
      groupSearchResults.value = [];
      return;
    }
    isLoadingGroupSearch.value = true;
    groupSearchError.value = null;
    try {
      const response = await axiosInstance.get<PaginatedGroupResponse>(`/groups/?search=${query}`);
      // The backend returns a paginated response, so we need the .results
      groupSearchResults.value = response.data.results;
    } catch (err: any) {
      console.error('Error searching groups:', err);
      groupSearchError.value = err.response?.data?.detail || 'Failed to search for groups.';
      groupSearchResults.value = []; // Clear results on error
    } finally {
      isLoadingGroupSearch.value = false;
    }
  }

  async function fetchGroupDetails(groupSlug: string) {
    // <-- Parameter changed to string slug
    isLoadingGroup.value = true
    groupError.value = null
    resetGroupFeedState()

    try {
      // Use the new slug parameter in the URL
      const response = await axiosInstance.get<Group>(`/groups/${groupSlug}/`)
      currentGroup.value = response.data
      // Pass the numeric ID from the response to fetch the posts
      await fetchGroupPosts(response.data.slug)
    } catch (err: any) {
      // Update the error message to be more helpful
      console.error(`Error fetching details for group slug ${groupSlug}:`, err)
      groupError.value = err.response?.data?.detail || 'Failed to load group details.'
      currentGroup.value = null
    } finally {
      isLoadingGroup.value = false
    }
  }

  async function fetchGroupPosts(groupSlug: string, url: string | null = null) {
    if (isLoadingGroupPosts.value) return
    isLoadingGroupPosts.value = true
    groupError.value = null

    try {
      const apiUrl = url || `/groups/${groupSlug}/status-posts/`
      const response = await axiosInstance.get<CursorPaginatedGroupPostResponse>(apiUrl)

      if (!url) {
        groupPosts.value = response.data.results
      } else {
        groupPosts.value.push(...response.data.results)
      }
      groupPostsNextCursor.value = response.data.next
    } catch (err: any) {
      console.error(`Error fetching posts for group ${groupSlug}:`, err)
      groupError.value = err.response?.data?.detail || 'Failed to load group posts.'
    } finally {
      isLoadingGroupPosts.value = false
    }
  }

  async function fetchNextPageOfGroupPosts() {
    if (groupPostsNextCursor.value && !isLoadingGroupPosts.value && currentGroup.value) {
      await fetchGroupPosts(currentGroup.value.slug, groupPostsNextCursor.value)
    }
  }

  function addPostToGroupFeed(post: Post) {
    if (currentGroup.value && post.group?.id === currentGroup.value.id) {
      groupPosts.value.unshift(post)
    }
  }

  async function fetchGroups(url: string | null = null) {
    if (isLoadingAllGroups.value) return
    isLoadingAllGroups.value = true
    allGroupsError.value = null
    try {
      const apiUrl = url || '/groups/'
      const response = await axiosInstance.get<PaginatedGroupResponse>(apiUrl)

      if (!url) {
        allGroups.value = response.data.results
      } else {
        allGroups.value.push(...response.data.results)
      }

      allGroupsNextPageUrl.value = response.data.next
      allGroupsHasNextPage.value = response.data.next !== null
    } catch (err: any) {
      console.error('Error fetching groups:', err)
      allGroupsError.value = err.response?.data?.detail || 'Failed to load groups.'
    } finally {
      isLoadingAllGroups.value = false
    }
  }

  async function fetchNextPageOfGroups() {
    if (allGroupsNextPageUrl.value && !isLoadingAllGroups.value) {
      await fetchGroups(allGroupsNextPageUrl.value)
    }
  }

  async function createGroup(groupData: {
    name: string
    description: string
    privacy_level: 'public' | 'private'
  }): Promise<Group | null> {
    isCreatingGroup.value = true
    createGroupError.value = null
    try {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        createGroupError.value = 'You must be logged in to create a group.'
        return null
      }
      const response = await axiosInstance.post<Group>('/groups/', groupData)
      const newGroup = response.data
      allGroups.value.unshift(newGroup)
      return newGroup
    } catch (err: any) {
      console.error('Error creating group:', err)
      let errorMessage = 'Failed to create group. Please check the details.'
      if (err.response && err.response.data) {
        const errorData = err.response.data
        if (typeof errorData === 'object' && errorData !== null) {
          const fieldErrors = []
          if (errorData.name?.[0]) fieldErrors.push(`Name: ${errorData.name[0]}`)
          if (errorData.description?.[0])
            fieldErrors.push(`Description: ${errorData.description[0]}`)
          if (errorData.privacy_level?.[0])
            fieldErrors.push(`Privacy Level: ${errorData.privacy_level[0]}`)
          if (fieldErrors.length > 0) {
            errorMessage = fieldErrors.join(' ')
          } else if (errorData.detail) {
            errorMessage = errorData.detail
          }
        } else if (typeof errorData === 'string') {
          errorMessage = errorData
        }
        createGroupError.value = errorMessage
      } else {
        createGroupError.value = errorMessage
      }
      return null
    } finally {
      isCreatingGroup.value = false
    }
  }

  async function joinGroup(groupSlug: string): Promise<boolean> {
    isJoiningLeaving.value = true
    joinLeaveError.value = null
    try {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        joinLeaveError.value = 'You must be logged in to join a group.'
        return false
      }
      await axiosInstance.post(`/groups/${groupSlug}/membership/`)
      if (currentGroup.value && currentGroup.value.slug === groupSlug) {
        currentGroup.value.is_member = true
        currentGroup.value.member_count++
      }
      const groupInAllList = allGroups.value.find((g) => g.slug === groupSlug)
      if (groupInAllList) {
        groupInAllList.is_member = true
        groupInAllList.member_count++
      }
      return true
    } catch (err: any) {
      console.error(`Error joining group ${groupSlug}:`, err)
      joinLeaveError.value = err.response?.data?.detail || 'Failed to join group.'
      return false
    } finally {
      isJoiningLeaving.value = false
    }
  }

  async function leaveGroup(groupSlug: string): Promise<boolean> {
    isJoiningLeaving.value = true
    joinLeaveError.value = null
    try {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        joinLeaveError.value = 'You must be logged in to leave a group.'
        return false
      }
      await axiosInstance.delete(`/groups/${groupSlug}/membership/`)
      if (currentGroup.value && currentGroup.value.slug === groupSlug) {
        currentGroup.value.is_member = false
        currentGroup.value.member_count--
      }
      const groupInAllList = allGroups.value.find((g) => g.slug === groupSlug)
      if (groupInAllList) {
        groupInAllList.is_member = false
        groupInAllList.member_count--
      }
      return true
    } catch (err: any) {
      console.error(`Error leaving group ${groupSlug}:`, err)
      joinLeaveError.value = err.response?.data?.detail || 'Failed to leave group.'
      return false
    } finally {
      isJoiningLeaving.value = false
    }
  }

  // --- ADDITION: NEW DELETE GROUP ACTION ---
  async function deleteGroup(groupSlug: string): Promise<boolean> {
    isDeletingGroup.value = true
    deleteGroupError.value = null
    try {
      await axiosInstance.delete(`/groups/${groupSlug}/`)
      // After a successful delete, remove it from the list of all groups
      allGroups.value = allGroups.value.filter((g) => g.slug !== groupSlug)
      // And clear the current group if it's the one we deleted
      if (currentGroup.value && currentGroup.value.slug === groupSlug) {
        currentGroup.value = null
      }
      return true
    } catch (err: any) {
      console.error(`Error deleting group ${groupSlug}:`, err)
      deleteGroupError.value = err.response?.data?.detail || 'Could not delete the group.'
      return false
    } finally {
      isDeletingGroup.value = false
    }
  }

  async function transferOwnership(groupSlug: string, newOwnerId: number): Promise<boolean> {
    isTransferringOwnership.value = true
    transferOwnershipError.value = null
    try {
      const payload = { new_owner_id: newOwnerId }
      await axiosInstance.post(`/groups/${groupSlug}/transfer-ownership/`, payload)

      // After a successful transfer, we need to update the local state.
      if (currentGroup.value && currentGroup.value.slug === groupSlug) {
        // The current user is no longer the creator
        currentGroup.value.is_creator = false
        // We don't know the new creator's full user object without another API call,
        // so for now, we can clear the page or just update the flag.
        // Fetching the group details again is the most robust solution.
        await fetchGroupDetails(groupSlug)
      }

      return true
    } catch (err: any) {
      console.error(`Error transferring ownership for group ${groupSlug}:`, err)
      transferOwnershipError.value = err.response?.data?.detail || 'Could not transfer ownership.'
      return false
    } finally {
      isTransferringOwnership.value = false
    }
  }

  return {
    // State
    currentGroup,
    groupPosts,
    isLoadingGroup,
    groupError,
    isJoiningLeaving,
    joinLeaveError,
    isLoadingGroupPosts,
    groupPostsNextCursor,
    allGroups,
    isLoadingAllGroups,
    allGroupsError,
    allGroupsHasNextPage,
    allGroupsNextPageUrl,
    isCreatingGroup,
    createGroupError,
    // ADDITION: New State
    isDeletingGroup,
    deleteGroupError,
    isTransferringOwnership,
    transferOwnershipError,
    groupSearchResults,
    isLoadingGroupSearch,
    groupSearchError,

    // Actions
    fetchGroupDetails,
    fetchGroupPosts,
    fetchNextPageOfGroupPosts,
    fetchGroups,
    fetchNextPageOfGroups,
    createGroup,
    joinGroup,
    leaveGroup,
    addPostToGroupFeed,
    // ADDITION: New Action
    deleteGroup,
    transferOwnership,
    searchGroups,

    $reset,

    // Exported Reset Functions
    resetGroupFeedState,
    resetAllGroupsState,
  }
})
