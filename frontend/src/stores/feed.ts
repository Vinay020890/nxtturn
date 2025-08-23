// C:\Users\Vinay\Project\frontend\src\stores\feed.ts

import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import { useAuthStore } from './auth'
import { useProfileStore } from './profile'
import { useGroupStore } from './group'

// --- Interfaces ---
interface PostAuthor {
  id: number
  username: string
  first_name: string
  last_name: string
  picture: string | null
}
export interface PostMedia {
  id: number
  media_type: 'image' | 'video'
  file_url: string
}
export interface PollOption {
  id: number
  text: string
  vote_count: number
}
export interface Poll {
  id: number
  question: string
  options: PollOption[]
  total_votes: number
  user_vote: number | null
}
export interface Post {
  id: number
  post_type: string
  author: PostAuthor
  created_at: string
  updated_at: string
  title: string | null
  content: string | null
  media: PostMedia[]
  poll: Poll | null
  like_count: number
  comment_count?: number
  is_liked_by_user: boolean
  content_type_id: number
  object_id: number
  isLiking?: boolean
  isDeleting?: boolean
  isUpdating?: boolean
  group: { id: number; name: string; slug: string } | null
  is_saved: boolean
}

// Interface for Cursor-based Pagination Response
interface CursorPaginatedResponse {
  next: string | null
  previous: string | null
  results: Post[]
}

// Interface for Offset-based Pagination Response (like for Saved Posts)
interface OffsetPaginatedResponse {
  count: number
  next: string | null
  previous: string | null
  results: Post[]
}

export const useFeedStore = defineStore('feed', () => {
  // --- State ---
  const mainFeedPosts = ref<Post[]>([])
  const mainFeedNextCursor = ref<string | null>(null)
  const isLoadingMainFeed = ref(false)
  const mainFeedError = ref<string | null>(null)
  const isRefreshingMainFeed = ref(false)
  const newPostsFromRefresh = ref<Post[]>([])

  const savedPosts = ref<Post[]>([])
  const savedPostsNextPageUrl = ref<string | null>(null)
  const isLoadingSavedPosts = ref(false)
  const savedPostsError = ref<string | null>(null)

  const createPostError = ref<string | null>(null)
  const isCreatingPost = ref(false)
  const deletePostError = ref<string | null>(null)
  const updatePostError = ref<string | null>(null)
  const singlePost = ref<Post | null>(null)
  const isLoadingSinglePost = ref(false)
  const singlePostError = ref<string | null>(null)

  const searchResultsPosts = ref<Post[]>([])
  const isLoadingSearchResults = ref(false)
  const searchError = ref<string | null>(null)

  // === $reset() method implementation ===
  function $reset() {
    mainFeedPosts.value = []
    mainFeedNextCursor.value = null
    isLoadingMainFeed.value = false
    mainFeedError.value = null

    savedPosts.value = []
    savedPostsNextPageUrl.value = null
    isLoadingSavedPosts.value = false
    savedPostsError.value = null

    createPostError.value = null
    isCreatingPost.value = false
    deletePostError.value = null
    updatePostError.value = null
    singlePost.value = null
    isLoadingSinglePost.value = false
    singlePostError.value = null

    searchResultsPosts.value = []
    isLoadingSearchResults.value = false
    searchError.value = null
  }

  // --- Targeted Reset Functions ---
  function resetMainFeedState() {
    mainFeedPosts.value = []
    mainFeedNextCursor.value = null
    isLoadingMainFeed.value = false
    mainFeedError.value = null
    isRefreshingMainFeed.value = false // <-- ADD THIS
    newPostsFromRefresh.value = [] // <-- ADD THIS
    console.log('Main feed state has been reset.')
  }

  function resetSavedPostsState() {
    savedPosts.value = []
    savedPostsNextPageUrl.value = null
    isLoadingSavedPosts.value = false
    savedPostsError.value = null
    console.log('Saved posts state has been reset.')
  }

  // --- Helper Functions ---
  function findPostInAnyList(postId: number): Post | undefined {
    const groupStore = useGroupStore()
    const profileStore = useProfileStore()

    const listsToSearch = [
      mainFeedPosts.value,
      savedPosts.value,
      groupStore.groupPosts,
      profileStore.userPosts,
      searchResultsPosts.value,
      singlePost.value ? [singlePost.value] : [],
    ]

    for (const list of listsToSearch) {
      if (list && Array.isArray(list)) {
        const post = list.find((p) => p.id === postId)
        if (post) {
          return post
        }
      }
    }
    return undefined
  }

  // --- NEW: CENTRALIZED UPDATE ACTION ---
  function applyPostUpdate(postId: number, updates: Partial<Post>) {
    const groupStore = useGroupStore()
    const profileStore = useProfileStore()

    const listsToUpdate = [
      mainFeedPosts.value,
      savedPosts.value,
      groupStore.groupPosts,
      profileStore.userPosts,
      searchResultsPosts.value,
    ]

    for (const list of listsToUpdate) {
      if (list && Array.isArray(list)) {
        const index = list.findIndex((p) => p.id === postId)
        if (index !== -1) {
          list[index] = { ...list[index], ...updates }
        }
      }
    }

    if (singlePost.value && singlePost.value.id === postId) {
      singlePost.value = { ...singlePost.value, ...updates }
    }
  }

  // --- Actions ---
  // --- NEW ACTION TO FIX PROFILE PICTURE BUG ---
  // --- THIS FUNCTION IS MODIFIED TO BE MORE REACTIVE ---
  function updateAuthorDetailsInAllPosts(authorId: number, updates: Partial<PostAuthor>) {
    const profileStore = useProfileStore()
    const groupStore = useGroupStore()

    const updateList = (list: Post[]) => {
      return list.map((post) => {
        if (post.author.id === authorId) {
          // Create a new post object with the updated author info
          return {
            ...post,
            author: { ...post.author, ...updates },
          }
        }
        return post
      })
    }

    // Re-assign the entire array to trigger reactivity
    mainFeedPosts.value = updateList(mainFeedPosts.value)
    savedPosts.value = updateList(savedPosts.value)
    profileStore.userPosts = updateList(profileStore.userPosts) // This is the key line for the bug
    groupStore.groupPosts = updateList(groupStore.groupPosts)
    searchResultsPosts.value = updateList(searchResultsPosts.value)

    if (singlePost.value && singlePost.value.author.id === authorId) {
      singlePost.value = {
        ...singlePost.value,
        author: { ...singlePost.value.author, ...updates },
      }
    }
  }

  async function searchPosts(query: string) {
    if (!query) {
      searchResultsPosts.value = []
      return
    }
    isLoadingSearchResults.value = true
    searchError.value = null
    try {
      interface SearchPostResponse {
        results: Post[]
      }

      const response = await axiosInstance.get<SearchPostResponse>(`/posts/?search=${query}`)
      searchResultsPosts.value = response.data.results.map((post) => ({
        ...post,
        isLiking: false,
        isDeleting: false,
        isUpdating: false,
      }))
    } catch (err: any) {
      searchError.value = err.response?.data?.detail || err.message || 'Failed to search posts.'
      console.error('FeedStore: Error searching posts:', err)
    } finally {
      isLoadingSearchResults.value = false
    }
  }

  async function fetchFeed(url: string | null = null) {
    if (isLoadingMainFeed.value) return
    isLoadingMainFeed.value = true
    mainFeedError.value = null

    try {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        isLoadingMainFeed.value = false
        mainFeedError.value = 'Authentication required to fetch feed.'
        return
      }
      const apiUrl = url || '/feed/'
      const response = await axiosInstance.get<CursorPaginatedResponse>(apiUrl)
      const fetchedPosts = response.data.results.map((post) => ({
        ...post,
        isLiking: false,
        isDeleting: false,
        isUpdating: false,
      }))

      if (!url) {
        mainFeedPosts.value = fetchedPosts
      } else {
        mainFeedPosts.value.push(...fetchedPosts)
      }
      mainFeedNextCursor.value = response.data.next
    } catch (err: any) {
      mainFeedError.value = err.response?.data?.detail || err.message || 'Failed to fetch feed.'
      console.error('FeedStore: Error fetching main feed:', err)
    } finally {
      isLoadingMainFeed.value = false
    }
  }

  // --- NEW: Action to show the new posts ---
  function showNewPosts() {
    mainFeedPosts.value.unshift(...newPostsFromRefresh.value)
    newPostsFromRefresh.value = []
  }

  // --- NEW: Smart Refresh Action ---
    // --- THIS IS THE CORRECTED VERSION ---
  async function refreshMainFeed() {
    if (isRefreshingMainFeed.value) return;

    // Use the main loader for the initial fetch, but not for silent refreshes.
    const isInitialLoad = mainFeedPosts.value.length === 0;
    if (isInitialLoad) {
      isLoadingMainFeed.value = true;
    }
    isRefreshingMainFeed.value = true;
    mainFeedError.value = null;

    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) return;

      const response = await axiosInstance.get<CursorPaginatedResponse>('/feed/');
      const freshPosts = response.data.results;

      if (isInitialLoad) {
        // --- INITIAL LOAD LOGIC ---
        // On the very first load, put posts directly into the main feed.
        mainFeedPosts.value = freshPosts;
        newPostsFromRefresh.value = []; // Ensure this is empty
      } else {
        // --- BACKGROUND REFRESH LOGIC ---
        const existingPostIds = new Set(mainFeedPosts.value.map(p => p.id));
        const genuinelyNewPosts = freshPosts.filter(p => !existingPostIds.has(p.id));

        if (genuinelyNewPosts.length > 0) {
          newPostsFromRefresh.value = genuinelyNewPosts;
        }

        const freshPostsMap = new Map(freshPosts.map(p => [p.id, p]));
        mainFeedPosts.value = mainFeedPosts.value.map(oldPost => {
          const freshVersion = freshPostsMap.get(oldPost.id);
          return freshVersion ? freshVersion : oldPost;
        });
      }

      // Always update the cursor
      mainFeedNextCursor.value = response.data.next;

    } catch (err: any) {
      console.error('FeedStore: Error refreshing main feed:', err);
      if (isInitialLoad) {
        mainFeedError.value = err.response?.data?.detail || 'Failed to load feed.';
      }
    } finally {
      isRefreshingMainFeed.value = false;
      if (isInitialLoad) {
        isLoadingMainFeed.value = false;
      }
    }
  }

  async function fetchNextPageOfMainFeed() {
    if (mainFeedNextCursor.value && !isLoadingMainFeed.value) {
      await fetchFeed(mainFeedNextCursor.value)
    }
  }

  async function fetchSavedPosts(url: string | null = null) {
    if (isLoadingSavedPosts.value) return
    isLoadingSavedPosts.value = true
    savedPostsError.value = null

    try {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        isLoadingSavedPosts.value = false
        savedPostsError.value = 'Authentication required to fetch saved posts.'
        return
      }
      const apiUrl = url || '/posts/saved/'
      const response = await axiosInstance.get<OffsetPaginatedResponse>(apiUrl)
      const fetchedPosts = response.data.results.map((post) => ({
        ...post,
        isLiking: false,
        isDeleting: false,
        isUpdating: false,
      }))

      if (!url) {
        savedPosts.value = fetchedPosts
      } else {
        savedPosts.value.push(...fetchedPosts)
      }
      savedPostsNextPageUrl.value = response.data.next
    } catch (err: any) {
      savedPostsError.value =
        err.response?.data?.detail || err.message || 'Failed to fetch saved posts.'
      console.error('FeedStore: Failed to fetch saved posts:', err)
    } finally {
      isLoadingSavedPosts.value = false
    }
  }

  async function fetchNextPageOfSavedPosts() {
    if (savedPostsNextPageUrl.value && !isLoadingSavedPosts.value) {
      await fetchSavedPosts(savedPostsNextPageUrl.value)
    }
  }

  async function fetchPostById(postId: number) {
    isLoadingSinglePost.value = true
    singlePostError.value = null
    singlePost.value = null
    try {
      const response = await axiosInstance.get<Post>(`/posts/${postId}/`)
      singlePost.value = response.data
    } catch (err: any) {
      console.error(`FeedStore: Error fetching post ID ${postId}:`, err)
      singlePostError.value = err.response?.data?.detail || `Post with ID ${postId} not found.`
    } finally {
      isLoadingSinglePost.value = false
    }
  }

  async function ensureFullPostData(postId: number) {
    if (
      singlePost.value &&
      singlePost.value.id === postId &&
      typeof singlePost.value.comment_count !== 'undefined'
    ) {
      return
    }

    const existingPost = findPostInAnyList(postId)
    if (existingPost && typeof existingPost.comment_count !== 'undefined') {
      singlePost.value = existingPost
      return
    }

    await fetchPostById(postId)
  }

  async function createPost(postData: FormData): Promise<Post | null> {
    isCreatingPost.value = true
    createPostError.value = null
    try {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        createPostError.value = 'User not authenticated. Please login to post.'
        return null
      }
      const response = await axiosInstance.post<Post>('/posts/', postData)
      const newPost = { ...response.data, isLiking: false, isDeleting: false, isUpdating: false }
      const groupStore = useGroupStore()

      if (mainFeedPosts.value.length > 0) {
        mainFeedPosts.value.unshift(newPost)
      }

      if (newPost.group && newPost.group.id === groupStore.currentGroup?.id) {
        groupStore.addPostToGroupFeed(newPost)
      }
      return newPost
    } catch (err: any) {
      console.error('FeedStore: Error creating post:', err)
      let errorMessage = 'An unexpected error occurred while creating the post.'
      if (err.response && err.response.data) {
        const errorData = err.response.data
        if (typeof errorData === 'object' && errorData !== null) {
          const errorKeys = [
            'images',
            'videos',
            'content',
            'poll_data',
            'detail',
            'non_field_errors',
            'group',
          ]
          const firstErrorKey = errorKeys.find((key) => errorData[key])
          if (firstErrorKey) {
            const errorValue = errorData[firstErrorKey]
            errorMessage = Array.isArray(errorValue) ? errorValue[0] : String(errorValue)
          }
        } else if (typeof errorData === 'string' && errorData) {
          errorMessage = errorData
        }
      } else if (err.message) {
        errorMessage = err.message
      }
      createPostError.value = errorMessage
      return null
    } finally {
      isCreatingPost.value = false
    }
  }

  // --- REFACTORED to use applyPostUpdate ---
  async function toggleLike(
    postId: number,
    postType: string,
    contentTypeId: number,
    objectId: number,
  ) {
    const postToUpdate = findPostInAnyList(postId)
    if (!postToUpdate || postToUpdate.isLiking) return

    const originalState = {
      is_liked_by_user: postToUpdate.is_liked_by_user,
      like_count: postToUpdate.like_count,
    }

    applyPostUpdate(postId, { isLiking: true })

    // Optimistic UI update
    const newLikeCount = originalState.like_count + (originalState.is_liked_by_user ? -1 : 1)
    applyPostUpdate(postId, {
      is_liked_by_user: !originalState.is_liked_by_user,
      like_count: newLikeCount,
    })

    try {
      const response = await axiosInstance.post<{ liked: boolean; like_count: number }>(
        `/content/${contentTypeId}/${objectId}/like/`,
      )
      // Authoritative update from server
      applyPostUpdate(postId, {
        is_liked_by_user: response.data.liked,
        like_count: response.data.like_count,
      })
    } catch (err: any) {
      console.error('FeedStore: Error toggling like:', err)
      // Revert on failure
      applyPostUpdate(postId, originalState)
      mainFeedError.value = err.response?.data?.detail || 'Failed to toggle like.'
    } finally {
      applyPostUpdate(postId, { isLiking: false })
    }
  }

  function incrementCommentCount(postId: number, postType: string) {
    const postToUpdate = findPostInAnyList(postId)
    if (postToUpdate) {
      applyPostUpdate(postId, { comment_count: (postToUpdate.comment_count || 0) + 1 })
    }
  }

  function decrementCommentCount(postId: number, postType: string) {
    const postToUpdate = findPostInAnyList(postId)
    if (postToUpdate && postToUpdate.comment_count) {
      applyPostUpdate(postId, { comment_count: Math.max(0, postToUpdate.comment_count - 1) })
    }
  }

  async function deletePost(postId: number, postType: string): Promise<boolean> {
    const postToDelete = findPostInAnyList(postId)
    if (postToDelete) {
      applyPostUpdate(postId, { isDeleting: true })
    }

    try {
      await axiosInstance.delete(`/posts/${postId}/`)
      mainFeedPosts.value = mainFeedPosts.value.filter((p) => p.id !== postId)
      savedPosts.value = savedPosts.value.filter((p) => p.id !== postId)

      const groupStore = useGroupStore()
      groupStore.groupPosts = groupStore.groupPosts.filter((p) => p.id !== postId)

      const profileStore = useProfileStore()
      profileStore.userPosts = profileStore.userPosts.filter((p) => p.id !== postId)

      searchResultsPosts.value = searchResultsPosts.value.filter((p) => p.id !== postId)

      if (singlePost.value && singlePost.value.id === postId) {
        singlePost.value = null
      }
      return true
    } catch (err: any) {
      deletePostError.value = err.response?.data?.detail || err.message || 'Failed to delete post.'
      console.error('FeedStore: Error deleting post:', err)
      if (postToDelete) {
        applyPostUpdate(postId, { isDeleting: false })
      }
      return false
    }
  }

  async function updatePost(
    postId: number,
    postType: string,
    formData: FormData,
  ): Promise<boolean> {
    const postToUpdate = findPostInAnyList(postId)
    if (postToUpdate) {
      applyPostUpdate(postId, { isUpdating: true })
    }

    if (!postToUpdate) {
      console.warn(`updatePost: Post with ID ${postId} not found in any active store.`)
      return false
    }
    try {
      const response = await axiosInstance.patch<Post>(`/posts/${postId}/`, formData)
      const updatedData = { ...response.data, isUpdating: false, isLiking: postToUpdate.isLiking }
      applyPostUpdate(postId, updatedData)
      return true
    } catch (err: any) {
      updatePostError.value = err.response?.data?.detail || 'Failed to update post.'
      console.error('FeedStore: Error updating post:', err)
      return false
    } finally {
      if (postToUpdate) applyPostUpdate(postId, { isUpdating: false })
    }
  }

  async function castVote(postId: number, pollId: number, optionId: number): Promise<void> {
    const postToUpdate = findPostInAnyList(postId)
    if (!postToUpdate || !postToUpdate.poll) {
      console.warn(`castVote: Post with ID ${postId} or its poll not found.`)
      return
    }

    const poll = postToUpdate.poll
    const originalPollState = JSON.parse(JSON.stringify(poll))

    // Optimistic UI update logic...
    const previousVoteId = poll.user_vote
    const isRetracting = previousVoteId === optionId
    if (previousVoteId !== null) {
      const prevOption = poll.options.find((o) => o.id === previousVoteId)
      if (prevOption) prevOption.vote_count--
    }
    if (!isRetracting) {
      const newOption = poll.options.find((o) => o.id === optionId)
      if (newOption) newOption.vote_count++
    }
    if (isRetracting) {
      poll.total_votes--
      poll.user_vote = null
    } else {
      if (previousVoteId === null) poll.total_votes++
      poll.user_vote = optionId
    }

    try {
      const apiUrl = `/polls/${pollId}/options/${optionId}/vote/`
      const response = isRetracting
        ? await axiosInstance.delete<Post>(apiUrl)
        : await axiosInstance.post<Post>(apiUrl)
      applyPostUpdate(postId, response.data)
    } catch (err: any) {
      console.error('FeedStore: Failed to cast/retract vote:', err)
      mainFeedError.value = err.response?.data?.detail || 'Failed to update vote.'
      applyPostUpdate(postId, { poll: originalPollState })
    }
  }

  // --- REFACTORED to use applyPostUpdate ---
  async function toggleSavePost(postId: number): Promise<void> {
    const postToUpdate = findPostInAnyList(postId)
    if (!postToUpdate) {
      console.warn(`toggleSavePost: Post with ID ${postId} not found.`)
      return
    }

    const originalIsSaved = postToUpdate.is_saved

    // Optimistic UI update for all instances
    applyPostUpdate(postId, { is_saved: !originalIsSaved })

    try {
      const response = await axiosInstance.post<Post>(`/posts/${postId}/save/`)
      const updatedPostFromServer = response.data

      // Authoritative update for all instances
      applyPostUpdate(postId, { is_saved: updatedPostFromServer.is_saved })

      // Now, manage the savedPosts list separately based on the authoritative response
      if (updatedPostFromServer.is_saved) {
        // Add to saved list if it's not already there
        const existsInSaved = savedPosts.value.some((p) => p.id === postId)
        if (!existsInSaved) {
          savedPosts.value.unshift(postToUpdate) // Use the locally available full object
        }
      } else {
        // Remove from saved list
        savedPosts.value = savedPosts.value.filter((p) => p.id !== postId)
      }
    } catch (err: any) {
      console.error(`FeedStore: Error toggling save status for post ID ${postId}:`, err)
      // Revert on failure
      applyPostUpdate(postId, { is_saved: originalIsSaved })
      mainFeedError.value = err.response?.data?.detail || 'Failed to toggle save status.'
    }
  }

  return {
    // State
    mainFeedPosts,
    isRefreshingMainFeed, // <-- ADD THIS
    newPostsFromRefresh,
    mainFeedNextCursor,
    isLoadingMainFeed,
    mainFeedError,
    savedPosts,
    savedPostsNextPageUrl,
    isLoadingSavedPosts,
    savedPostsError,
    createPostError,
    isCreatingPost,
    deletePostError,
    updatePostError,
    singlePost,
    isLoadingSinglePost,
    singlePostError,
    searchResultsPosts,
    isLoadingSearchResults,
    searchError,
    // Actions
    fetchFeed,
    fetchNextPageOfMainFeed,
    fetchSavedPosts,
    fetchNextPageOfSavedPosts,
    fetchPostById,
    createPost,
    searchPosts,
    toggleLike,
    incrementCommentCount,
    decrementCommentCount,
    deletePost,
    updatePost,
    castVote,
    toggleSavePost,
    ensureFullPostData,
    $reset,
    resetMainFeedState,
    resetSavedPostsState,
    updateAuthorDetailsInAllPosts,
    refreshMainFeed,      // <-- ADD THIS
    showNewPosts,
  }
})
