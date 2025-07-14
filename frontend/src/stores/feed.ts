// C:\Users\Vinay\Project\frontend\src\stores\feed.ts

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import { useAuthStore } from './auth';
import { useProfileStore } from './profile'; // Imported for updateUserPost action
import { useGroupStore } from './group';

// --- Interfaces ---
interface PostAuthor {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  picture: string | null;
}
export interface PostMedia {
  id: number;
  media_type: 'image' | 'video';
  file_url: string;
}
export interface PollOption {
  id: number;
  text: string;
  vote_count: number;
}
export interface Poll {
  id: number;
  question: string;
  options: PollOption[];
  total_votes: number;
  user_vote: number | null;
}
export interface Post {
  id: number;
  post_type: string;
  author: PostAuthor;
  created_at: string;
  updated_at: string;
  title: string | null;
  content: string | null;
  media: PostMedia[];
  poll: Poll | null;
  like_count: number;
  comment_count?: number;
  is_liked_by_user: boolean;
  content_type_id: number;
  object_id: number;
  isLiking?: boolean;
  isDeleting?: boolean;
  isUpdating?: boolean;
  group: { id: number; name: string; } | null;
  is_saved: boolean;
}

// Interface for Cursor-based Pagination Response
interface CursorPaginatedResponse {
  next: string | null;
  previous: string | null;
  results: Post[];
}

// Interface for Offset-based Pagination Response (like for Saved Posts)
interface OffsetPaginatedResponse {
  count: number;
  next: string | null; // This 'next' will be a URL with ?page=X
  previous: string | null;
  results: Post[];
}


export const useFeedStore = defineStore('feed', () => {
  // --- State ---
  const mainFeedPosts = ref<Post[]>([]);
  const mainFeedNextCursor = ref<string | null>(null); // URL for the next cursor page
  const isLoadingMainFeed = ref(false);
  const mainFeedError = ref<string | null>(null);

  const savedPosts = ref<Post[]>([]);
  const savedPostsNextPageUrl = ref<string | null>(null); // URL for the next offset page
  const isLoadingSavedPosts = ref(false);
  const savedPostsError = ref<string | null>(null);

  const createPostError = ref<string | null>(null);
  const isCreatingPost = ref(false);
  const deletePostError = ref<string | null>(null);
  const updatePostError = ref<string | null>(null);
  const singlePost = ref<Post | null>(null);
  const isLoadingSinglePost = ref(false);
  const singlePostError = ref<string | null>(null);

  // === $reset() method implementation ===
  function $reset() {
    mainFeedPosts.value = [];
    mainFeedNextCursor.value = null;
    isLoadingMainFeed.value = false;
    mainFeedError.value = null;

    savedPosts.value = [];
    savedPostsNextPageUrl.value = null;
    isLoadingSavedPosts.value = false;
    savedPostsError.value = null;

    createPostError.value = null;
    isCreatingPost.value = false;
    deletePostError.value = null;
    updatePostError.value = null;
    singlePost.value = null;
    isLoadingSinglePost.value = false;
    singlePostError.value = null;
  }
  // ==========================================

  // --- Targeted Reset Functions ---
  function resetMainFeedState() {
    mainFeedPosts.value = [];
    mainFeedNextCursor.value = null;
    isLoadingMainFeed.value = false;
    mainFeedError.value = null;
    console.log('Main feed state has been reset.');
  }

  function resetSavedPostsState() {
    savedPosts.value = [];
    savedPostsNextPageUrl.value = null;
    isLoadingSavedPosts.value = false;
    savedPostsError.value = null;
    console.log('Saved posts state has been reset.');
  }

  // --- Actions ---

  async function fetchFeed(url: string | null = null) {
    if (isLoadingMainFeed.value) return;
    isLoadingMainFeed.value = true;
    mainFeedError.value = null;

    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        isLoadingMainFeed.value = false;
        mainFeedError.value = "Authentication required to fetch feed.";
        return;
      }
      
      const apiUrl = url || '/feed/';

      const response = await axiosInstance.get<CursorPaginatedResponse>(apiUrl);
      const fetchedPosts = response.data.results.map(post => ({
          ...post,
          isLiking: false,
          isDeleting: false,
          isUpdating: false
      }));
      
      if (!url) {
        mainFeedPosts.value = fetchedPosts;
      } else {
        mainFeedPosts.value.push(...fetchedPosts);
      }

      mainFeedNextCursor.value = response.data.next;

    } catch (err: any) {
      mainFeedError.value = err.response?.data?.detail || err.message || 'Failed to fetch feed.';
      console.error("FeedStore: Error fetching main feed:", err);
    } finally {
      isLoadingMainFeed.value = false;
    }
  }

  async function fetchNextPageOfMainFeed() {
    if (mainFeedNextCursor.value && !isLoadingMainFeed.value) {
      await fetchFeed(mainFeedNextCursor.value);
    }
  }

  async function fetchSavedPosts(url: string | null = null) {
    if (isLoadingSavedPosts.value) return;
    isLoadingSavedPosts.value = true;
    savedPostsError.value = null;

    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        isLoadingSavedPosts.value = false;
        savedPostsError.value = "Authentication required to fetch saved posts.";
        return;
      }

      const apiUrl = url || '/posts/saved/';

      const response = await axiosInstance.get<OffsetPaginatedResponse>(apiUrl);
      const fetchedPosts = response.data.results.map(post => ({
        ...post,
        isLiking: false,
        isDeleting: false,
        isUpdating: false
      }));

      if (!url) {
        savedPosts.value = fetchedPosts;
      } else {
        savedPosts.value.push(...fetchedPosts);
      }

      savedPostsNextPageUrl.value = response.data.next;

    } catch (err: any) {
      savedPostsError.value = err.response?.data?.detail || err.message || 'Failed to fetch saved posts.';
      console.error("FeedStore: Failed to fetch saved posts:", err);
    } finally {
      isLoadingSavedPosts.value = false;
    }
  }

  async function fetchNextPageOfSavedPosts() {
    if (savedPostsNextPageUrl.value && !isLoadingSavedPosts.value) {
      await fetchSavedPosts(savedPostsNextPageUrl.value);
    }
  }

  async function fetchPostById(postId: number) {
    isLoadingSinglePost.value = true;
    singlePostError.value = null;
    singlePost.value = null;
    try {
      const response = await axiosInstance.get<Post>(`/posts/${postId}/`);
      singlePost.value = response.data;
    } catch (err: any) {
      console.error(`FeedStore: Error fetching post ID ${postId}:`, err);
      singlePostError.value = err.response?.data?.detail || `Post with ID ${postId} not found.`;
    } finally {
      isLoadingSinglePost.value = false;
    }
  }

  async function createPost(postData: FormData): Promise<Post | null> {
    isCreatingPost.value = true;
    createPostError.value = null;
    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        createPostError.value = "User not authenticated. Please login to post.";
        return null;
      }
      const response = await axiosInstance.post<Post>('/posts/', postData);
      const newPost = { ...response.data, isLiking: false, isDeleting: false, isUpdating: false };
      const groupStore = useGroupStore();

      mainFeedPosts.value.unshift(newPost);

      if (newPost.group && newPost.group.id === groupStore.currentGroup?.id) {
        groupStore.addPostToGroupFeed(newPost);
      }
      return newPost;
    } catch (err: any) {
      console.error("FeedStore: Error creating post:", err);
      let errorMessage = 'An unexpected error occurred while creating the post.';
      if (err.response && err.response.data) {
        const errorData = err.response.data;
        if (typeof errorData === 'object' && errorData !== null) {
          const errorKeys = ['images', 'videos', 'content', 'poll_data', 'detail', 'non_field_errors', 'group'];
          const firstErrorKey = errorKeys.find(key => errorData[key]);
          if (firstErrorKey) {
            const errorValue = errorData[firstErrorKey];
            errorMessage = Array.isArray(errorValue) ? errorValue[0] : String(errorValue);
          }
        } else if (typeof errorData === 'string' && errorData) {
          errorMessage = errorData;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      createPostError.value = errorMessage;
      return null;
    } finally {
      isCreatingPost.value = false;
    }
  }

  async function toggleLike(postId: number, postType: string, contentTypeId: number, objectId: number) {
    const updatePostInList = (list: Post[], updatedPost: Post) => {
      const index = list.findIndex(p => p.id === updatedPost.id && p.post_type === updatedPost.post_type);
      if (index !== -1) {
        list[index] = { ...list[index], ...updatedPost };
      }
    };

    const postToUpdate = mainFeedPosts.value.find(p => p.id === postId) ||
                         singlePost.value ||
                         savedPosts.value.find(p => p.id === postId);

    if (postToUpdate && !postToUpdate.isLiking) {
      postToUpdate.isLiking = true;
      const originalLikedStatus = postToUpdate.is_liked_by_user;
      const originalLikeCount = postToUpdate.like_count;
      postToUpdate.is_liked_by_user = !postToUpdate.is_liked_by_user;
      postToUpdate.like_count += postToUpdate.is_liked_by_user ? 1 : -1;

      try {
        const apiUrl = `/content/${contentTypeId}/${objectId}/like/`;
        const response = await axiosInstance.post<Post>(apiUrl);

        updatePostInList(mainFeedPosts.value, response.data);
        updatePostInList(savedPosts.value, response.data);
        if (singlePost.value && singlePost.value.id === response.data.id) {
          singlePost.value = { ...singlePost.value, ...response.data };
        }
      } catch (err: any) {
        postToUpdate.is_liked_by_user = originalLikedStatus;
        postToUpdate.like_count = originalLikeCount;
        mainFeedError.value = err.response?.data?.detail || err.message || 'Failed to toggle like.';
        console.error("FeedStore: Error toggling like:", err);
        throw err;
      } finally {
        if (postToUpdate) postToUpdate.isLiking = false;
      }
    } else if (!postToUpdate) {
      try {
        const apiUrl = `/content/${contentTypeId}/${objectId}/like/`;
        await axiosInstance.post(apiUrl);
      } catch (err: any) {
        console.error(`FeedStore: Error toggling like for non-local object ${objectId}:`, err);
        throw err;
      }
    }
  }

  function incrementCommentCount(postId: number, postType: string) {
    const findAndIncrement = (list: Post[]) => {
      const post = list.find(p => p.id === postId && p.post_type === postType);
      if (post) post.comment_count = (post.comment_count || 0) + 1;
    };
    findAndIncrement(mainFeedPosts.value);
    findAndIncrement(savedPosts.value);
    if (singlePost.value && singlePost.value.id === postId) {
      singlePost.value.comment_count = (singlePost.value.comment_count || 0) + 1;
    }
  }

  async function deletePost(postId: number, postType: string): Promise<boolean> {
      const markAsDeleting = (list: Post[]) => {
          const post = list.find(p => p.id === postId && p.post_type === postType);
          if (post) post.isDeleting = true;
      };
      markAsDeleting(mainFeedPosts.value);
      markAsDeleting(savedPosts.value);

      try {
          if (postType.toLowerCase() !== 'statuspost') {
              throw new Error(`Deletion for post_type '${postType}' is not supported here.`);
          }
          await axiosInstance.delete(`/posts/${postId}/`);

          mainFeedPosts.value = mainFeedPosts.value.filter(p => !(p.id === postId && p.post_type === postType));
          savedPosts.value = savedPosts.value.filter(p => !(p.id === postId && p.post_type === postType));
          
          if (singlePost.value && singlePost.value.id === postId) {
            singlePost.value = null;
          }
          return true;
      } catch (err: any) {
          deletePostError.value = err.response?.data?.detail || err.message || 'Failed to delete post.';
          console.error("FeedStore: Error deleting post:", err);
          return false;
      }
  }

  async function updatePost(postId: number, postType: string, formData: FormData): Promise<boolean> {
      const markAsUpdating = (list: Post[]) => {
          const post = list.find(p => p.id === postId && p.post_type === postType);
          if (post) post.isUpdating = true;
      };
      markAsUpdating(mainFeedPosts.value);
      markAsUpdating(savedPosts.value);
      if (singlePost.value && singlePost.value.id === postId) {
        singlePost.value.isUpdating = true;
      }

      try {
          if (postType.toLowerCase() !== 'statuspost') {
              throw new Error(`Update for post_type '${postType}' is not supported here.`);
          }
          const response = await axiosInstance.patch<Post>(`/posts/${postId}/`, formData);
          const updatedData = { ...response.data, isUpdating: false };

          const updateInList = (list: Post[]) => {
              const index = list.findIndex(p => p.id === updatedData.id && p.post_type === updatedData.post_type);
              if (index !== -1) {
                  list[index] = { ...list[index], ...updatedData };
              }
          };
          updateInList(mainFeedPosts.value);
          updateInList(savedPosts.value);

          if (singlePost.value && singlePost.value.id === postId) {
            singlePost.value = { ...singlePost.value, ...updatedData };
          }
          const profileStore = useProfileStore();
          profileStore.updateUserPost(response.data);
          return true;
      } catch (err: any) {
          updatePostError.value = err.response?.data?.detail || 'Failed to update post.';
          console.error("FeedStore: Error updating post:", err);
          return false;
      } finally {
          const revertUpdating = (list: Post[]) => {
              const post = list.find(p => p.id === postId && p.post_type === postType);
              if (post) post.isUpdating = false;
          };
          revertUpdating(mainFeedPosts.value);
          revertUpdating(savedPosts.value);
          if (singlePost.value && singlePost.value.id === postId) {
            singlePost.value.isUpdating = false;
          }
      }
  }
  
  async function castVote(pollId: number, optionId: number): Promise<void> {
    const postToUpdate = mainFeedPosts.value.find(p => p.poll?.id === pollId) ||
                         singlePost.value ||
                         savedPosts.value.find(p => p.poll?.id === pollId);

    if (!postToUpdate || !postToUpdate.poll) {
        console.warn(`Post with poll ID ${pollId} not found in store for voting.`);
        return;
    }

    const poll = postToUpdate.poll;
    const previousVoteId = poll.user_vote;
    const isRetracting = previousVoteId === optionId;
    const originalPollState = JSON.parse(JSON.stringify(poll));

    if (previousVoteId !== null) {
      const prevOption = poll.options.find(o => o.id === previousVoteId);
      if (prevOption) prevOption.vote_count--;
    }
    if (!isRetracting) {
      const newOption = poll.options.find(o => o.id === optionId);
      if (newOption) newOption.vote_count++;
    }
    if (isRetracting) {
      poll.total_votes--;
      poll.user_vote = null;
    } else {
      if (previousVoteId === null) {
        poll.total_votes++;
      }
      poll.user_vote = optionId;
    }

    try {
      let response;
      const apiUrl = `/polls/${pollId}/options/${optionId}/vote/`;
      if (isRetracting) {
        response = await axiosInstance.delete<Post>(apiUrl);
      } else {
        response = await axiosInstance.post<Post>(apiUrl);
      }
      const updatedPost = response.data;

      const updateInList = (list: Post[]) => {
        const index = list.findIndex(p => p.id === updatedPost.id);
        if (index !== -1) {
          list[index] = { ...list[index], ...updatedPost };
        }
      };
      updateInList(mainFeedPosts.value);
      updateInList(savedPosts.value);
      if (singlePost.value && singlePost.value.id === updatedPost.id) {
        singlePost.value = { ...singlePost.value, ...updatedPost };
      }

    } catch (err: any) {
      console.error("Failed to cast/retract vote:", err);
      mainFeedError.value = err.response?.data?.detail || "Failed to update vote.";
      const revertPollInList = (list: Post[]) => {
        const post = list.find(p => p.poll?.id === pollId);
        if (post) post.poll = originalPollState;
      };
      revertPollInList(mainFeedPosts.value);
      revertPollInList(savedPosts.value);
      if (singlePost.value?.poll?.id === pollId) {
        singlePost.value.poll = originalPollState;
      }
    }
  }

  async function toggleSavePost(postId: number): Promise<void> {
    const postToUpdateInMainFeed = mainFeedPosts.value.find(p => p.id === postId);
    const postToUpdateInSaved = savedPosts.value.find(p => p.id === postId);
    const postToUpdateInSingle = singlePost.value && singlePost.value.id === postId ? singlePost.value : null;

    const originalIsSaved = postToUpdateInMainFeed?.is_saved ?? postToUpdateInSaved?.is_saved ?? postToUpdateInSingle?.is_saved ?? false;

    if (postToUpdateInMainFeed) postToUpdateInMainFeed.is_saved = !postToUpdateInMainFeed.is_saved;
    if (postToUpdateInSaved) postToUpdateInSaved.is_saved = !postToUpdateInSaved.is_saved;
    if (postToUpdateInSingle) postToUpdateInSingle.is_saved = !postToUpdateInSingle.is_saved;

    try {
      const response = await axiosInstance.post<Post>(`/posts/${postId}/save/`);
      const updatedPost = response.data;

      const updatePostInList = (list: Post[], postData: Post) => {
        const index = list.findIndex(p => p.id === postData.id);
        if (index !== -1) {
          list[index] = { ...list[index], ...postData };
        }
      };

      updatePostInList(mainFeedPosts.value, updatedPost);
      if (singlePost.value && singlePost.value.id === updatedPost.id) {
        singlePost.value = { ...singlePost.value, ...updatedPost };
      }

      if (updatedPost.is_saved) {
        if (!postToUpdateInSaved) {
          // New saved posts will appear on the next full fetch of the saved posts page.
        }
      } else {
        savedPosts.value = savedPosts.value.filter(p => p.id !== updatedPost.id);
      }

    } catch (err: any) {
      console.error(`FeedStore: Error toggling save status for post ID ${postId}:`, err);
      mainFeedError.value = err.response?.data?.detail || err.message || 'Failed to toggle save status.';
      if (postToUpdateInMainFeed) postToUpdateInMainFeed.is_saved = originalIsSaved;
      if (postToUpdateInSaved) postToUpdateInSaved.is_saved = originalIsSaved;
      if (postToUpdateInSingle) postToUpdateInSingle.is_saved = originalIsSaved;
    }
  }


  return {
    // State
    mainFeedPosts,
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

    // Actions
    fetchFeed,
    fetchNextPageOfMainFeed,
    fetchSavedPosts,
    fetchNextPageOfSavedPosts,

    fetchPostById,
    createPost,
    toggleLike,
    incrementCommentCount,
    deletePost,
    updatePost,
    castVote,
    toggleSavePost,

    $reset,

    // Exported Reset Functions
    resetMainFeedState,
    resetSavedPostsState,
  };
});