// C:\Users\Vinay\Project\frontend\src\stores\feed.ts

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import { useAuthStore } from './auth';
import { useProfileStore } from './profile';
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
  next: string | null;
  previous: string | null;
  results: Post[];
}


export const useFeedStore = defineStore('feed', () => {
  // --- State ---
  const mainFeedPosts = ref<Post[]>([]);
  const mainFeedNextCursor = ref<string | null>(null);
  const isLoadingMainFeed = ref(false);
  const mainFeedError = ref<string | null>(null);

  const savedPosts = ref<Post[]>([]);
  const savedPostsNextPageUrl = ref<string | null>(null);
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
    const groupStore = useGroupStore();
    const profileStore = useProfileStore();
    const postToUpdate = 
        mainFeedPosts.value.find(p => p.id === postId) ||
        savedPosts.value.find(p => p.id === postId) ||
        groupStore.groupPosts.find(p => p.id === postId) ||
        profileStore.userPosts.find(p => p.id === postId) ||
        (singlePost.value?.id === postId ? singlePost.value : null);

    if (!postToUpdate) {
        console.warn(`toggleLike: Post with ID ${postId} not found in any active store.`);
        return;
    }
    if (postToUpdate.isLiking) return;
    postToUpdate.isLiking = true;
    const originalIsLiked = postToUpdate.is_liked_by_user;
    const originalLikeCount = postToUpdate.like_count;
    postToUpdate.is_liked_by_user = !postToUpdate.is_liked_by_user;
    postToUpdate.like_count += postToUpdate.is_liked_by_user ? 1 : -1;
    try {
      const response = await axiosInstance.post<Post>(`/content/${contentTypeId}/${objectId}/like/`);
      Object.assign(postToUpdate, response.data, { isLiking: false });
    } catch (err: any) {
      console.error("FeedStore: Error toggling like:", err);
      postToUpdate.is_liked_by_user = originalIsLiked;
      postToUpdate.like_count = originalLikeCount;
      mainFeedError.value = err.response?.data?.detail || err.message || 'Failed to toggle like.';
    } finally {
      if (postToUpdate) postToUpdate.isLiking = false;
    }
  }

  function incrementCommentCount(postId: number, postType: string) {
    const groupStore = useGroupStore();
    const profileStore = useProfileStore();
    const postToUpdate = 
        mainFeedPosts.value.find(p => p.id === postId) ||
        savedPosts.value.find(p => p.id === postId) ||
        groupStore.groupPosts.find(p => p.id === postId) ||
        profileStore.userPosts.find(p => p.id === postId) ||
        (singlePost.value?.id === postId ? singlePost.value : null);
        
    if (postToUpdate) {
      postToUpdate.comment_count = (postToUpdate.comment_count || 0) + 1;
    }
  }

  async function deletePost(postId: number, postType: string): Promise<boolean> {
      const groupStore = useGroupStore();
      const profileStore = useProfileStore();

      const findAndMark = (postList: Post[], id: number) => {
        const post = postList.find(p => p.id === id);
        if (post) post.isDeleting = true;
        return post;
      };
      
      findAndMark(mainFeedPosts.value, postId);
      findAndMark(savedPosts.value, postId);
      findAndMark(groupStore.groupPosts, postId);
      findAndMark(profileStore.userPosts, postId);

      try {
          await axiosInstance.delete(`/posts/${postId}/`);

          mainFeedPosts.value = mainFeedPosts.value.filter(p => p.id !== postId);
          savedPosts.value = savedPosts.value.filter(p => p.id !== postId);
          groupStore.groupPosts = groupStore.groupPosts.filter(p => p.id !== postId);
          profileStore.userPosts = profileStore.userPosts.filter(p => p.id !== postId);
          
          if (singlePost.value && singlePost.value.id === postId) {
            singlePost.value = null;
          }
          return true;
      } catch (err: any) {
          deletePostError.value = err.response?.data?.detail || err.message || 'Failed to delete post.';
          console.error("FeedStore: Error deleting post:", err);

          const findAndUnmark = (list: Post[], id: number) => {
            const post = list.find(p => p.id === id);
            if (post) post.isDeleting = false;
          };
          findAndUnmark(mainFeedPosts.value, postId);
          findAndUnmark(savedPosts.value, postId);
          findAndUnmark(groupStore.groupPosts, postId);
          findAndUnmark(profileStore.userPosts, postId);
          return false;
      }
  }

  async function updatePost(postId: number, postType: string, formData: FormData): Promise<boolean> {
      const groupStore = useGroupStore();
      const profileStore = useProfileStore();
      
      const findAndMark = (postList: Post[], id: number) => {
        const post = postList.find(p => p.id === id);
        if (post) post.isUpdating = true;
        return post;
      };

      const postToUpdate = findAndMark(mainFeedPosts.value, postId) ||
                         findAndMark(savedPosts.value, postId) ||
                         findAndMark(groupStore.groupPosts, postId) ||
                         findAndMark(profileStore.userPosts, postId) ||
                         (singlePost.value?.id === postId ? findAndMark([singlePost.value], postId) : null);

      if (!postToUpdate) {
        console.warn(`updatePost: Post with ID ${postId} not found in any active store.`);
        return false;
      }

      try {
          const response = await axiosInstance.patch<Post>(`/posts/${postId}/`, formData);
          const updatedData = { ...response.data, isUpdating: false, isLiking: postToUpdate.isLiking };
          
          Object.assign(postToUpdate, updatedData);

          return true;
      } catch (err: any) {
          updatePostError.value = err.response?.data?.detail || 'Failed to update post.';
          console.error("FeedStore: Error updating post:", err);
          return false;
      } finally {
          if (postToUpdate) postToUpdate.isUpdating = false;
      }
  }
  
  async function castVote(pollId: number, optionId: number): Promise<void> {
    const groupStore = useGroupStore();
    const profileStore = useProfileStore();

    const postToUpdate = 
        mainFeedPosts.value.find(p => p.poll?.id === pollId) ||
        savedPosts.value.find(p => p.poll?.id === pollId) ||
        groupStore.groupPosts.find(p => p.poll?.id === pollId) ||
        profileStore.userPosts.find(p => p.poll?.id === pollId) ||
        (singlePost.value?.poll?.id === pollId ? singlePost.value : null);

    if (!postToUpdate || !postToUpdate.poll) {
        console.warn(`castVote: Post with poll ID ${pollId} not found in any active store.`);
        try {
            await axiosInstance.post<Post>(`/polls/${pollId}/options/${optionId}/vote/`);
        } catch(err) {
            console.error('castVote: API call failed for non-local poll.', err);
        }
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
      const updatedPostData = response.data;
      
      Object.assign(postToUpdate, updatedPostData);

    } catch (err: any) {
      console.error("FeedStore: Failed to cast/retract vote:", err);
      mainFeedError.value = err.response?.data?.detail || "Failed to update vote.";
      Object.assign(postToUpdate.poll, originalPollState);
    }
  }

  async function toggleSavePost(postId: number): Promise<void> {
    const groupStore = useGroupStore();
    const profileStore = useProfileStore();

    const postToUpdate = 
        mainFeedPosts.value.find(p => p.id === postId) ||
        savedPosts.value.find(p => p.id === postId) ||
        groupStore.groupPosts.find(p => p.id === postId) ||
        profileStore.userPosts.find(p => p.id === postId) ||
        (singlePost.value?.id === postId ? singlePost.value : null);
    
    if (!postToUpdate) {
        console.warn(`toggleSavePost: Post with ID ${postId} not found in any active store.`);
        return;
    }

    const originalIsSaved = postToUpdate.is_saved;
    postToUpdate.is_saved = !postToUpdate.is_saved;

    try {
      const response = await axiosInstance.post<Post>(`/posts/${postId}/save/`);
      const updatedPost = response.data;
      
      Object.assign(postToUpdate, updatedPost);

      if (!updatedPost.is_saved) {
        savedPosts.value = savedPosts.value.filter(p => p.id !== updatedPost.id);
      }

    } catch (err: any) {
      console.error(`FeedStore: Error toggling save status for post ID ${postId}:`, err);
      mainFeedError.value = err.response?.data?.detail || err.message || 'Failed to toggle save status.';
      postToUpdate.is_saved = originalIsSaved;
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