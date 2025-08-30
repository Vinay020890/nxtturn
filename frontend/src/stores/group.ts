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
  description: string | null
  creator: User
  members: User[]
  member_count: number
  membership_status: 'creator' | 'member' | 'pending' | 'none'
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

export interface GroupJoinRequest {
  id: number
  user: User
  group: number
  status: 'pending' | 'approved' | 'denied'
  created_at: string
}

export interface GroupBlock {
  id: number
  user: User
  group: number
  blocked_by: User
  created_at: string
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

  const isDeletingGroup = ref(false)
  const deleteGroupError = ref<string | null>(null)

  const isTransferringOwnership = ref(false)
  const transferOwnershipError = ref<string | null>(null)

  const joinRequests = ref<GroupJoinRequest[]>([])
  const isLoadingRequests = ref(false)
  const requestsError = ref<string | null>(null)
  const isManagingRequest = ref(false)
  const manageRequestError = ref<string | null>(null)

  const blockedUsers = ref<GroupBlock[]>([])
  const isLoadingBlockedUsers = ref(false)
  const blockedUsersError = ref<string | null>(null)
  const isUnblockingUser = ref(false)
  const unblockUserError = ref<string | null>(null)

  const groupSearchResults = ref<Group[]>([])
  const isLoadingGroupSearch = ref(false)
  const groupSearchError = ref<string | null>(null)

  const isUpdatingGroup = ref(false)
  const updateGroupError = ref<string | null>(null)

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
    isDeletingGroup.value = false
    deleteGroupError.value = null
  }

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
  async function fetchGroupDetails(groupSlug: string) {
    isLoadingGroup.value = true
    groupError.value = null
    // Reset state for the new group
    currentGroup.value = null
    groupPosts.value = []
    groupPostsNextCursor.value = null

    try {
      // This call will now always succeed for existing groups
      const response = await axiosInstance.get<Group>(`/groups/${groupSlug}/`)
      currentGroup.value = response.data

      // *** THIS IS THE KEY LOGIC CHANGE ***
      // Only fetch posts if the group is public, OR if the user is a member/creator of a private group.
      const canViewPosts =
        response.data.privacy_level === 'public' ||
        ['creator', 'member'].includes(response.data.membership_status)

      if (canViewPosts) {
        await fetchGroupPosts(response.data.slug)
      }
    } catch (err: any) {
      console.error(`Error fetching details for group slug ${groupSlug}:`, err)
      groupError.value = err.response?.data?.detail || 'Failed to load group details.'
      currentGroup.value = null
    } finally {
      isLoadingGroup.value = false
    }
  }

  async function fetchBlockedUsers(groupSlug: string) {
    isLoadingBlockedUsers.value = true
    blockedUsersError.value = null
    try {
      const response = await axiosInstance.get(`/groups/${groupSlug}/blocks/`)
      blockedUsers.value = response.data.results
    } catch (err: any) {
      console.error(`Error fetching blocked users for group ${groupSlug}:`, err)
      blockedUsersError.value = err.response?.data?.detail || 'Failed to load blocked users.'
    } finally {
      isLoadingBlockedUsers.value = false
    }
  }

  // In C:\Users\Vinay\Project\frontend\src\stores\group.ts

  async function unblockUser(groupSlug: string, userId: number): Promise<boolean> {
    isUnblockingUser.value = true
    unblockUserError.value = null
    try {
      // This is the real API call to the endpoint we just built and tested.
      await axiosInstance.delete(`/groups/${groupSlug}/blocks/${userId}/`)

      // On success, optimistically remove the user from the local list.
      blockedUsers.value = blockedUsers.value.filter((block) => block.user.id !== userId)

      return true
    } catch (err: any) {
      console.error(`Error unblocking user ${userId} from group ${groupSlug}:`, err)
      unblockUserError.value = err.response?.data?.detail || 'Failed to unblock user.'
      return false
    } finally {
      isUnblockingUser.value = false
    }
  }

  async function searchGroups(query: string) {
    if (!query.trim()) {
      groupSearchResults.value = []
      return
    }
    isLoadingGroupSearch.value = true
    groupSearchError.value = null
    try {
      const response = await axiosInstance.get<PaginatedGroupResponse>(`/groups/?search=${query}`)
      groupSearchResults.value = response.data.results
    } catch (err: any) {
      console.error('Error searching groups:', err)
      groupSearchError.value = err.response?.data?.detail || 'Failed to search for groups.'
      groupSearchResults.value = []
    } finally {
      isLoadingGroupSearch.value = false
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
      const response = await axiosInstance.post(`/groups/${groupSlug}/membership/`)
      const outcomeStatus = response.data.status
      const handleStateUpdate = (group: Group) => {
        if (outcomeStatus === 'request sent') {
          group.membership_status = 'pending'
        } else if (outcomeStatus === 'member added') {
          group.membership_status = 'member'
          group.member_count++
        }
      }
      if (currentGroup.value && currentGroup.value.slug === groupSlug) {
        handleStateUpdate(currentGroup.value)
      }
      const groupInAllList = allGroups.value.find((g) => g.slug === groupSlug)
      if (groupInAllList) {
        handleStateUpdate(groupInAllList)
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
      const handleStateUpdate = (group: Group) => {
        group.membership_status = 'none'
        group.member_count--
      }
      if (currentGroup.value && currentGroup.value.slug === groupSlug) {
        handleStateUpdate(currentGroup.value)
      }
      const groupInAllList = allGroups.value.find((g) => g.slug === groupSlug)
      if (groupInAllList) {
        handleStateUpdate(groupInAllList)
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

  async function deleteGroup(groupSlug: string): Promise<boolean> {
    isDeletingGroup.value = true
    deleteGroupError.value = null
    try {
      await axiosInstance.delete(`/groups/${groupSlug}/`)
      allGroups.value = allGroups.value.filter((g) => g.slug !== groupSlug)
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
      if (currentGroup.value && currentGroup.value.slug === groupSlug) {
        currentGroup.value.membership_status = 'member'
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

  async function fetchJoinRequests(groupSlug: string) {
    isLoadingRequests.value = true
    requestsError.value = null
    try {
      const response = await axiosInstance.get(`/groups/${groupSlug}/requests/`)
      joinRequests.value = response.data.results
    } catch (err: any) {
      console.error(`Error fetching join requests for group ${groupSlug}:`, err)
      requestsError.value = err.response?.data?.detail || 'Failed to load join requests.'
    } finally {
      isLoadingRequests.value = false
    }
  }

  // In C:\Users\Vinay\Project\frontend\src\stores\group.ts

  async function manageJoinRequest(
    groupSlug: string,
    requestId: number,
    // THIS IS THE FIX. We add the new action type here.
    action: 'approve' | 'deny' | 'deny_and_block',
  ): Promise<boolean> {
    isManagingRequest.value = true
    manageRequestError.value = null
    try {
      const payload = { action } // The rest of the function is already correct
      await axiosInstance.patch(`/groups/${groupSlug}/requests/${requestId}/`, payload)

      joinRequests.value = joinRequests.value.filter((req) => req.id !== requestId)

      if (action === 'approve' && currentGroup.value && currentGroup.value.slug === groupSlug) {
        currentGroup.value.member_count++
      }

      return true
    } catch (err: any) {
      console.error(`Error managing request ${requestId}:`, err)
      manageRequestError.value = err.response?.data?.detail || `Failed to ${action} request.`
      return false
    } finally {
      isManagingRequest.value = false
    }
  }

  async function updateGroupDetails(slug: string, data: { name: string; description?: string }) {
    isUpdatingGroup.value = true
    updateGroupError.value = null
    try {
      const response = await axiosInstance.patch<Group>(`/groups/${slug}/`, data)
      if (currentGroup.value && currentGroup.value.slug === slug) {
        currentGroup.value = response.data
      }
      return true
    } catch (error: any) {
      console.error('Failed to update group details:', error)
      let errorMessage = 'An unknown error occurred.'
      if (error.response?.data) {
        if (error.response.data.name) {
          errorMessage = `Name: ${error.response.data.name[0]}`
        } else if (error.response.data.detail) {
          errorMessage = error.response.data.detail
        }
      }
      updateGroupError.value = errorMessage
      return false
    } finally {
      isUpdatingGroup.value = false
    }
  }

  return {
    // --- Existing State ---
    currentGroup,
    groupPosts,
    isLoadingGroup,
    groupError,
    joinRequests,
    isLoadingRequests,
    requestsError,
    isManagingRequest,
    manageRequestError,
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
    isDeletingGroup,
    deleteGroupError,
    isTransferringOwnership,
    transferOwnershipError,
    groupSearchResults,
    isLoadingGroupSearch,
    groupSearchError,
    isUpdatingGroup,
    updateGroupError,

    // --- NEW STATE TO EXPOSE ---
    blockedUsers,
    isLoadingBlockedUsers,
    blockedUsersError,
    isUnblockingUser,
    unblockUserError,

    // --- Existing Actions ---
    fetchGroupDetails,
    fetchGroupPosts,
    fetchNextPageOfGroupPosts,
    fetchGroups,
    fetchNextPageOfGroups,
    createGroup,
    joinGroup,
    leaveGroup,
    addPostToGroupFeed,
    deleteGroup,
    transferOwnership,
    searchGroups,
    fetchJoinRequests,
    manageJoinRequest,
    updateGroupDetails,

    // --- NEW ACTIONS TO EXPOSE ---
    fetchBlockedUsers,
    unblockUser,

    // --- Existing Reset Functions ---
    $reset,
    resetGroupFeedState,
    resetAllGroupsState,
  }
})
