// C:\Users\Vinay\Project\frontend\src/stores/group.ts

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import type { User } from './auth';
import type { Post } from './feed';
import { useAuthStore } from './auth';

// --- Interface Definitions ---

export interface Group {
  id: number;
  name: string;
  description: string;
  creator: User;
  member_count: number;
  is_member: boolean;
  created_at: string;
  privacy_level: 'public' | 'private';
}

interface PaginatedGroupResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Group[];
}

interface CursorPaginatedGroupPostResponse {
  next: string | null;
  previous: string | null;
  results: Post[];
}

// --- Store Definition ---

export const useGroupStore = defineStore('group', () => {
  // --- State ---
  const currentGroup = ref<Group | null>(null);
  const groupPosts = ref<Post[]>([]);
  const isLoadingGroup = ref(false);
  const groupError = ref<string | null>(null);
  const isJoiningLeaving = ref(false);
  const joinLeaveError = ref<string | null>(null);

  const isLoadingGroupPosts = ref(false);
  const groupPostsNextCursor = ref<string | null>(null);

  const allGroups = ref<Group[]>([]);
  const isLoadingAllGroups = ref(false);
  const allGroupsError = ref<string | null>(null);
  const allGroupsNextPageUrl = ref<string | null>(null);
  const allGroupsHasNextPage = ref(false);
  
  const isCreatingGroup = ref(false);
  const createGroupError = ref<string | object | null>(null);

  function $reset() {
    currentGroup.value = null;
    groupPosts.value = [];
    isLoadingGroup.value = false;
    groupError.value = null;
    isJoiningLeaving.value = false;
    joinLeaveError.value = null;
    isLoadingGroupPosts.value = false;
    groupPostsNextCursor.value = null;

    allGroups.value = [];
    isLoadingAllGroups.value = false;
    allGroupsError.value = null;
    allGroupsNextPageUrl.value = null;
    allGroupsHasNextPage.value = false;

    isCreatingGroup.value = false;
    createGroupError.value = null;
  }

  // --- Targeted Reset Functions ---
  function resetGroupFeedState() {
    currentGroup.value = null;
    groupPosts.value = [];
    groupPostsNextCursor.value = null;
    isLoadingGroupPosts.value = false;
    groupError.value = null;
    console.log('Individual group feed state has been reset.');
  }

  function resetAllGroupsState() {
    allGroups.value = [];
    allGroupsNextPageUrl.value = null;
    allGroupsHasNextPage.value = false;
    isLoadingAllGroups.value = false;
    allGroupsError.value = null;
    console.log('"All Groups" discovery state has been reset.');
  }

  // --- Actions ---

  async function fetchGroupDetails(groupId: number) {
    isLoadingGroup.value = true;
    groupError.value = null;
    resetGroupFeedState(); 

    try {
      const response = await axiosInstance.get<Group>(`/groups/${groupId}/`);
      currentGroup.value = response.data;
      await fetchGroupPosts(groupId);
    } catch (err: any) {
      console.error(`Error fetching details for group ${groupId}:`, err);
      groupError.value = err.response?.data?.detail || 'Failed to load group details.';
      currentGroup.value = null;
    } finally {
      isLoadingGroup.value = false;
    }
  }

  async function fetchGroupPosts(groupId: number, url: string | null = null) {
    if (isLoadingGroupPosts.value) return;
    isLoadingGroupPosts.value = true;
    groupError.value = null;

    try {
      const apiUrl = url || `/groups/${groupId}/status-posts/`;
      const response = await axiosInstance.get<CursorPaginatedGroupPostResponse>(apiUrl);

      if (!url) {
        groupPosts.value = response.data.results;
      } else {
        groupPosts.value.push(...response.data.results);
      }
      groupPostsNextCursor.value = response.data.next;
    } catch (err: any) {
      console.error(`Error fetching posts for group ${groupId}:`, err);
      groupError.value = err.response?.data?.detail || 'Failed to load group posts.';
    } finally {
      isLoadingGroupPosts.value = false;
    }
  }

  async function fetchNextPageOfGroupPosts() {
    if (groupPostsNextCursor.value && !isLoadingGroupPosts.value && currentGroup.value) {
      await fetchGroupPosts(currentGroup.value.id, groupPostsNextCursor.value);
    }
  }

  function addPostToGroupFeed(post: Post) {
    if (currentGroup.value && post.group?.id === currentGroup.value.id) {
      groupPosts.value.unshift(post);
    }
  }

  async function fetchGroups(url: string | null = null) {
    if (isLoadingAllGroups.value) return;
    isLoadingAllGroups.value = true;
    allGroupsError.value = null;
    try {
      const apiUrl = url || '/groups/';
      const response = await axiosInstance.get<PaginatedGroupResponse>(apiUrl);
      
      if (!url) {
        allGroups.value = response.data.results;
      } else {
        allGroups.value.push(...response.data.results);
      }
      
      allGroupsNextPageUrl.value = response.data.next;
      allGroupsHasNextPage.value = response.data.next !== null;
    } catch (err: any) {
      console.error("Error fetching groups:", err);
      allGroupsError.value = err.response?.data?.detail || 'Failed to load groups.';
    } finally {
      isLoadingAllGroups.value = false;
    }
  }

  async function fetchNextPageOfGroups() {
    if (allGroupsNextPageUrl.value && !isLoadingAllGroups.value) {
      await fetchGroups(allGroupsNextPageUrl.value);
    }
  }

  async function createGroup(groupData: { name: string; description: string; privacy_level: 'public' | 'private' }): Promise<Group | null> {
    isCreatingGroup.value = true;
    createGroupError.value = null;
    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        createGroupError.value = "You must be logged in to create a group.";
        return null;
      }
      const response = await axiosInstance.post<Group>('/groups/', groupData);
      const newGroup = response.data;
      allGroups.value.unshift(newGroup);
      return newGroup;
    } catch (err: any) {
      console.error("Error creating group:", err);
      let errorMessage = 'Failed to create group. Please check the details.';
      if (err.response && err.response.data) {
        const errorData = err.response.data;
        if (typeof errorData === 'object' && errorData !== null) {
          const fieldErrors = [];
          if (errorData.name?.[0]) fieldErrors.push(`Name: ${errorData.name[0]}`);
          if (errorData.description?.[0]) fieldErrors.push(`Description: ${errorData.description[0]}`);
          if (errorData.privacy_level?.[0]) fieldErrors.push(`Privacy Level: ${errorData.privacy_level[0]}`);
          if (fieldErrors.length > 0) {
            errorMessage = fieldErrors.join(' ');
          } else if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } else if (typeof errorData === 'string') {
          errorMessage = errorData;
        }
        createGroupError.value = errorMessage;
      } else {
        createGroupError.value = errorMessage;
      }
      return null;
    } finally {
      isCreatingGroup.value = false;
    }
  }

  async function joinGroup(groupId: number): Promise<boolean> {
    isJoiningLeaving.value = true;
    joinLeaveError.value = null;
    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        joinLeaveError.value = "You must be logged in to join a group.";
        return false;
      }
      await axiosInstance.post(`/groups/${groupId}/membership/`);
      if (currentGroup.value && currentGroup.value.id === groupId) {
        currentGroup.value.is_member = true;
        currentGroup.value.member_count++;
      }
      const groupInAllList = allGroups.value.find(g => g.id === groupId);
      if (groupInAllList) {
        groupInAllList.is_member = true;
        groupInAllList.member_count++;
      }
      return true;
    } catch (err: any) {
      console.error(`Error joining group ${groupId}:`, err);
      joinLeaveError.value = err.response?.data?.detail || 'Failed to join group.';
      return false;
    } finally {
      isJoiningLeaving.value = false;
    }
  }

  async function leaveGroup(groupId: number): Promise<boolean> {
    isJoiningLeaving.value = true;
    joinLeaveError.value = null;
    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        joinLeaveError.value = "You must be logged in to leave a group.";
        return false;
      }
      await axiosInstance.delete(`/groups/${groupId}/membership/`);
      if (currentGroup.value && currentGroup.value.id === groupId) {
        currentGroup.value.is_member = false;
        currentGroup.value.member_count--;
      }
      const groupInAllList = allGroups.value.find(g => g.id === groupId);
      if (groupInAllList) {
        groupInAllList.is_member = false;
        groupInAllList.member_count--;
      }
      return true;
    } catch (err: any) {
      console.error(`Error leaving group ${groupId}:`, err);
      joinLeaveError.value = err.response?.data?.detail || 'Failed to leave group.';
      return false;
    } finally {
      isJoiningLeaving.value = false;
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
    $reset,

    // Exported Reset Functions
    resetGroupFeedState,
    resetAllGroupsState,
  };
});